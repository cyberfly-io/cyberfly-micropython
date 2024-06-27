import oryx_crypto
import os
import json
import base64
import pact_utils
import urequests as rt
import time
import gc


class Crypto:
    def gen_key_pair(self):
        sk = os.urandom(32)
        pk = oryx_crypto.ed25519generatepubkey(sk)
        return {"publicKey":pk.hex(), "secretKey":sk.hex()}
    
    def restore_key_from_secret(self, sk):
        pk = oryx_crypto.ed25519generatepubkey(bytes.fromhex(sk))
        return {"publicKey":pk.hex(), "secretKey":sk}
    
    def hash_bin(self, msg):
        msg_bin = oryx_crypto.blake2b(msg)
        return msg_bin
    
    def b64_url_encoded_hash(self, s):
        if isinstance(s, str):
            s = s.encode()
        encoded_string = base64.b64encode(s)
        encoded_string = encoded_string.replace(b'+', b'-')
        encoded_string = encoded_string.replace(b'/', b'_')
        encoded_string = encoded_string.rstrip(b'=')
        return encoded_string.decode('utf-8')
    
    def sign(self, msg, key_pair):
        hs_bin = self.hash_bin(msg)
        hsh = self.b64_url_encoded_hash(hs_bin)
        pk = bytes.fromhex(key_pair['publicKey'])
        sk = bytes.fromhex(key_pair['secretKey'])
        sig = oryx_crypto.ed25519sign(sk, pk, hs_bin)
        return {"hash": hsh, "sig": sig.hex(), "pubKey": key_pair['publicKey']}
    
    def sign_map(self, msg, kp):
        hs_bin = self.hash_bin(msg)
        hsh = self.b64_url_encoded_hash(hs_bin)
        if "publicKey" in kp.keys() and "secretKey" in kp.keys():
            return self.sign(msg, kp)
        else:
            return {"hash": hsh, "sig": None, "publicKey": kp['publicKey']}
            
    def attach_sig(self, msg, kp_array):
        hs_bin = self.hash_bin(msg)
        hsh = self.b64_url_encoded_hash(hs_bin)
        if len(kp_array) == 0:
            return [{"hash": hsh, "sig": None}]
        sig_list = []
        for kp in kp_array:
            sig_list.append(self.sign_map(msg, kp))
        return sig_list
    
    def verify(self, msg, public_key, sig):
        try:
            pub_key = bytes.fromhex(public_key)
            signature_bytes = bytes.fromhex(sig)
            oryx_crypto.ed25519verify(pub_key, signature_bytes, self.hash_bin(msg))
            return True
        except Exception as e:
            print(e)
            return False
    

class Api:
    def filter_sig(self, sig):
        s = sig.get('sig')
        if s is None:
            return {}
        return {"sig": sig.get('sig')}
    
    def mk_single_cmd(self, sigs, cmd):
        return {
                "hash": pact_utils.pull_check_hashs(sigs),
                "sigs": list(map(pact_utils.pull_sig, filter(self.filter_sig, sigs))),
                "cmd": cmd}
    
    def mk_public_send(self, cmds):
        return {"cmds": pact_utils.as_list(cmds)}
    
    
    def prepare_exec_cmd(self, pact_code, env_data={}, meta={}, network_id=None,
                             nonce=time.time(), key_pairs=[]):
        kp_array = pact_utils.as_list(key_pairs)
        signers = list(map(pact_utils.mk_signer, kp_array))
        cmd_json = {
                "networkId": network_id,
                "payload": {
                    "exec": {
                        "data": env_data,
                        "code": pact_code
                    }
                },
                "signers": signers,
                "meta": meta,
                "nonce": json.dumps(nonce)
            }
        cmd = json.dumps(cmd_json)
        sigs = Crypto().attach_sig(cmd, kp_array)
        return Api().mk_single_cmd(sigs, cmd)
    

class Lang:
    
    def mk_meta(self, sender, chain_id, gas_price, gas_limit, creation_time, ttl):
        return {"creationTime": creation_time, "ttl": ttl, "gasLimit":
                    gas_limit, "chainId": chain_id, "gasPrice": gas_price, "sender": sender}
    

class Fetch:
    def simple_poll_req_from_exec(self, exec_msg):
        cmds = exec_msg.get('cmds')
        if cmds is None:
            raise TypeError("expected key 'cmds' in object: " + json.dumps(exec_msg))
        rks = []
        for cmd in cmds:
            hsh = cmd.get('hash')
            if hsh is None:
                raise TypeError("malformed object, expected 'hash' key in every cmd: " + json.dumps(exec_msg))
            rks.append(hsh)
        return {"requestKeys": pact_utils.unique(rks)}
    
    def simple_listen_req_from_exec(self, exec_msg):
        cmds = exec_msg.get('cmds')
        if cmds is None:
            raise TypeError("expected key 'cmds' in object: " + json.dumps(exec_msg))
        rks = []
        for cmd in cmds:
            hsh = cmd.get('hash')
            if hsh is None:
                raise TypeError("malformed object, expected 'hash' key in every cmd: " + json.dumps(exec_msg))
            rks.append(hsh)
        return {"listen": rks[0]}
    
    def make_prepare_cmd(self, cmd):
        return Api().prepare_exec_cmd(cmd['pactCode'], cmd['envData'], cmd['meta'], cmd['networkId'],
                                                     cmd['nonce'], cmd['keyPairs'])
    
    
    def fetch_send_raw(self, send_cmd, api_host):
        if api_host is None:
            raise Exception("No apiHost provided")
        send_cmds = list(map(self.make_prepare_cmd, pact_utils.as_list(send_cmd)))
        return rt.post(api_host + '/api/v1/send', data=pact_utils.json_utf8(Api().mk_public_send(send_cmds)), headers=pact_utils.get_headers())
    
    
    def send(self, send_cmd, api_host):
            res = self.fetch_send_raw(send_cmd, api_host)
            return pact_utils.parse_res(res)
    
    def fetch_local_raw(self, local_cmd, api_host):
        if api_host is None:
            raise Exception("No apiHost provided")
        local_data = Api().prepare_exec_cmd(local_cmd['pactCode'], local_cmd['envData'],
                                                           local_cmd['meta'], local_cmd['networkId'],
                                                           local_cmd['nonce'], local_cmd['keyPairs'])
        gc.collect()
        res = rt.post(api_host + '/api/v1/local', data=pact_utils.json_utf8(local_data), headers=pact_utils.get_headers(), timeout=5)
        return res
    
    def local(self, local_cmd, api_host):
            res = self.fetch_local_raw(local_cmd, api_host)
            return pact_utils.parse_res(res)
    
    def fetch_poll_raw(self, poll_cmd, api_host):
        if api_host is None:
            raise Exception("No apiHost provided")
        return rt.post(api_host + '/api/v1/poll', data=pact_utils.json_utf8(poll_cmd), headers=pact_utils.get_headers())

    def poll(self, poll_cmd, api_host):
        res = self.fetch_poll_raw(poll_cmd, api_host)
        return pact_utils.parse_res(res)


    def fetch_listen_raw(self, listen_cmd, api_host):
        if api_host is None:
            raise Exception("No apiHost provided")
        return rt.post(api_host + '/api/v1/listen', data=pact_utils.json_utf8(listen_cmd), headers=pact_utils.get_headers())

    def listen(self, listen_cmd, api_host):
        res = self.fetch_listen_raw(listen_cmd, api_host)
        return pact_utils.parse_res(res)

    def send_signed(self, signed_cmd, api_host):
        cmd = {"cmds": [signed_cmd]}
        res = rt.post(api_host + '/api/v1/send', data=listen_cmd(cmd), headers=pact_utils.get_headers())
        return res.json()
    