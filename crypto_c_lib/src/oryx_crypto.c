// Include MicroPython API.
#include "py/obj.h"
#include "py/runtime.h"
#include "../../oryx-embedded/cyclone_crypto/hash/blake2b.h"
#include "../../oryx-embedded/cyclone_crypto/ecc/ed25519.h"

#define DIGEST_BLAKE2S_LEN 32
#define DIGEST_BLAKE2B_LEN 32

const mp_rom_error_text_t LEN_INVALIDE = "len invalide";
const mp_rom_error_text_t OPERATION_INVALIDE = "oper invalide";
const mp_rom_error_text_t SIGNATURE_INVALIDE = "sign invalide";


// const uint8_t X509_MG_EXTENSION_EXCHANGES[4] = {0x2a, 0x03, 0x04, 0x00};



// Blake2b
static mp_obj_t python_blake2bCompute(mp_obj_t message_data_obj) {

    // Prep message
    mp_buffer_info_t message_bufinfo;
    mp_get_buffer_raise(message_data_obj, &message_bufinfo, MP_BUFFER_READ);

    uint8_t digest_out[DIGEST_BLAKE2B_LEN];
    int res = blake2bCompute(0, 0, message_bufinfo.buf, message_bufinfo.len, digest_out, DIGEST_BLAKE2B_LEN);

    if(res != 0) {
        nlr_raise(mp_obj_new_exception_msg(&mp_type_Exception, DIGEST_BLAKE2B_LEN));
    }

    // Return bytes obj
    return mp_obj_new_bytes(digest_out, DIGEST_BLAKE2B_LEN);
}
static MP_DEFINE_CONST_FUN_OBJ_1(python_blake2bCompute_obj, python_blake2bCompute);

// Ed25519

// Calculer cle publique a partir de la cle privee
static mp_obj_t python_ed25519GeneratePublickey(mp_obj_t privateKey_obj) {

    // Charger cle privee, valider
    mp_buffer_info_t private_key_bufinfo;
    mp_get_buffer_raise(privateKey_obj, &private_key_bufinfo, MP_BUFFER_READ);
    if(private_key_bufinfo.len != ED25519_PRIVATE_KEY_LEN) {
        nlr_raise(mp_obj_new_exception_msg(&mp_type_ValueError, LEN_INVALIDE));
    }

    // Calculer cle publique
    uint8_t cle_publique[ED25519_PUBLIC_KEY_LEN];
    int res = ed25519GeneratePublicKey(private_key_bufinfo.buf, cle_publique);

    if(res != 0) {
        nlr_raise(mp_obj_new_exception_msg(&mp_type_Exception, OPERATION_INVALIDE));
    }

    // Return bytes obj
    return mp_obj_new_bytes(cle_publique, ED25519_PUBLIC_KEY_LEN);
}
static MP_DEFINE_CONST_FUN_OBJ_1(python_ed25519GeneratePublickey_obj, python_ed25519GeneratePublickey);

/*
    ed25519GenerateSignature(const uint8_t *privateKey,
        const uint8_t *publicKey, const void *message, size_t messageLen,
        const void *context, uint8_t contextLen, uint8_t flag, uint8_t *signature)
*/
static mp_obj_t python_ed25519Sign(mp_obj_t privateKey_obj, mp_obj_t publicKey_obj, mp_obj_t message_obj) {

    // Charger cle privee
    mp_buffer_info_t privatekey_bufinfo;
    mp_get_buffer_raise(privateKey_obj, &privatekey_bufinfo, MP_BUFFER_READ);
    if(privatekey_bufinfo.len != ED25519_PRIVATE_KEY_LEN) {
        nlr_raise(mp_obj_new_exception_msg(&mp_type_ValueError, LEN_INVALIDE));
    }

    // Charger cle publique
    mp_buffer_info_t publicKey_bufinfo;
    mp_get_buffer_raise(publicKey_obj, &publicKey_bufinfo, MP_BUFFER_READ);
    if(publicKey_bufinfo.len != ED25519_PUBLIC_KEY_LEN) {
        nlr_raise(mp_obj_new_exception_msg(&mp_type_ValueError, LEN_INVALIDE));
    }

    // Charger message
    mp_buffer_info_t message_bufinfo;
    mp_get_buffer_raise(message_obj, &message_bufinfo, MP_BUFFER_READ);

    // Preparer output
    const uint8_t flag = 0;
    uint8_t signature_out[ED25519_SIGNATURE_LEN];

    // Signer
    int res = ed25519GenerateSignature(
        privatekey_bufinfo.buf, publicKey_bufinfo.buf,
        message_bufinfo.buf, message_bufinfo.len,
        0, 0, // context
        flag, 
        signature_out
    );

    if(res != 0) {
        // Erreur de signature
        nlr_raise(mp_obj_new_exception_msg(&mp_type_Exception, OPERATION_INVALIDE));
    }

    // Nouveau objet Python bytes avec la signature
    return mp_obj_new_bytes(signature_out, ED25519_SIGNATURE_LEN);
}
static MP_DEFINE_CONST_FUN_OBJ_3(python_ed25519Sign_obj, python_ed25519Sign);

/*
error_t ed25519VerifySignature(const uint8_t *publicKey, const void *message,
   size_t messageLen, const void *context, uint8_t contextLen, uint8_t flag,
   const uint8_t *signature);
*/
static mp_obj_t python_ed25519Verify(mp_obj_t publicKey_obj, mp_obj_t signature_obj, mp_obj_t message_obj) {

    mp_buffer_info_t publicKey_bufinfo;
    mp_get_buffer_raise(publicKey_obj, &publicKey_bufinfo, MP_BUFFER_READ);

    if(publicKey_bufinfo.len != 32) {
        nlr_raise(mp_obj_new_exception_msg(&mp_type_ValueError, LEN_INVALIDE));
    }

    mp_buffer_info_t signature_bufinfo;
    mp_get_buffer_raise(signature_obj, &signature_bufinfo, MP_BUFFER_READ);

    if(signature_bufinfo.len != 64) {
        nlr_raise(mp_obj_new_exception_msg(&mp_type_ValueError, LEN_INVALIDE));
    }

    mp_buffer_info_t message_bufinfo;
    mp_get_buffer_raise(message_obj, &message_bufinfo, MP_BUFFER_READ);

    const uint8_t flag = 0;

    int res = ed25519VerifySignature(
        publicKey_bufinfo.buf,
        message_bufinfo.buf, message_bufinfo.len,
        0, 0, // context
        flag, 
        signature_bufinfo.buf
    );

    if(res != 0) {
        // Erreur de signature
        nlr_raise(mp_obj_new_exception_msg(&mp_type_Exception, SIGNATURE_INVALIDE));
    }

    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_3(python_ed25519Verify_obj, python_ed25519Verify);


// Define all properties of the module.
// Table entries are key/value pairs of the attribute name (a string)
// and the MicroPython object reference.
// All identifiers and strings are written as MP_QSTR_xxx and will be
// optimized to word-sized integers by the build system (interned strings).
static const mp_rom_map_elem_t oryxcrypto_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_oryx_crypto) },
    { MP_ROM_QSTR(MP_QSTR_blake2b), MP_ROM_PTR(&python_blake2bCompute_obj) },
    { MP_ROM_QSTR(MP_QSTR_ed25519sign), MP_ROM_PTR(&python_ed25519Sign_obj) },
    { MP_ROM_QSTR(MP_QSTR_ed25519verify), MP_ROM_PTR(&python_ed25519Verify_obj) },
    { MP_ROM_QSTR(MP_QSTR_ed25519generatepubkey), MP_ROM_PTR(&python_ed25519GeneratePublickey_obj) },
  
};
static MP_DEFINE_CONST_DICT(oryxcrypto_module_globals, oryxcrypto_module_globals_table);

// Define module object.
const mp_obj_module_t oryxcrypto_user_cmodule = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&oryxcrypto_module_globals,
};

// Register the module to make it available in Python.
MP_REGISTER_MODULE(MP_QSTR_oryx_crypto, oryxcrypto_user_cmodule);
