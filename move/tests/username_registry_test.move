#[test_only]
module aptos_send::username_registry_test {
    use std::string;
    use std::signer;
    use aptos_framework::account;
    use aptos_send::username_registry;

    #[test(admin = @aptos_send, user = @0x456)]
    public fun test_username_registration(admin: &signer, user: &signer) {
        // Initialize the registry
        username_registry::initialize(admin);
        
        // Register a username
        let username = string::utf8(b"alice");
        username_registry::register_username(user, username);
        
        // Verify the username was registered
        let user_addr = signer::address_of(user);
        let resolved_addr = username_registry::get_address_by_username(username);
        assert!(resolved_addr == user_addr, 1);
        
        // Verify reverse lookup
        let resolved_username = username_registry::get_username_by_address(user_addr);
        assert!(resolved_username == username, 2);
        
        // Verify existence checks
        assert!(username_registry::username_exists(username), 3);
        assert!(username_registry::address_has_username(user_addr), 4);
    }

    #[test(admin = @aptos_send, user1 = @0x456, user2 = @0x789)]
    #[expected_failure(abort_code = 524289, location = aptos_send::username_registry)]
    public fun test_duplicate_username_fails(admin: &signer, user1: &signer, user2: &signer) {
        // Initialize the registry
        username_registry::initialize(admin);
        
        // Register a username with user1
        let username = string::utf8(b"alice");
        username_registry::register_username(user1, username);
        
        // Try to register the same username with user2 - should fail
        username_registry::register_username(user2, username);
    }

    #[test(admin = @aptos_send, user = @0x456)]
    public fun test_username_update(admin: &signer, user: &signer) {
        // Initialize the registry
        username_registry::initialize(admin);
        
        // Register initial username
        let old_username = string::utf8(b"alice");
        username_registry::register_username(user, old_username);
        
        // Update to new username
        let new_username = string::utf8(b"alice_updated");
        username_registry::update_username(user, new_username);
        
        // Verify the update
        let user_addr = signer::address_of(user);
        let resolved_addr = username_registry::get_address_by_username(new_username);
        assert!(resolved_addr == user_addr, 1);
        
        // Verify old username no longer exists
        assert!(!username_registry::username_exists(old_username), 2);
        
        // Verify new username exists
        assert!(username_registry::username_exists(new_username), 3);
    }
}
