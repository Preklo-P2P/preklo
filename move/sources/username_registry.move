module aptos_send::username_registry {
    use std::string::{Self, String};
    use std::signer;
    use std::error;
    use aptos_std::table::{Self, Table};
    use aptos_framework::account;
    use aptos_framework::event::{Self, EventHandle};

    /// Error codes
    const E_USERNAME_ALREADY_EXISTS: u64 = 1;
    const E_USERNAME_NOT_FOUND: u64 = 2;
    const E_NOT_AUTHORIZED: u64 = 3;
    const E_INVALID_USERNAME: u64 = 4;

    /// Username registry resource
    struct UsernameRegistry has key {
        /// Maps username to address
        username_to_address: Table<String, address>,
        /// Maps address to username
        address_to_username: Table<address, String>,
        /// Event handles
        username_registered_events: EventHandle<UsernameRegisteredEvent>,
        username_updated_events: EventHandle<UsernameUpdatedEvent>,
    }

    /// Events
    struct UsernameRegisteredEvent has drop, store {
        username: String,
        user_address: address,
    }

    struct UsernameUpdatedEvent has drop, store {
        old_username: String,
        new_username: String,
        user_address: address,
    }

    /// Initialize the username registry (called once by admin)
    public entry fun initialize(admin: &signer) {
        let admin_addr = signer::address_of(admin);
        assert!(admin_addr == @aptos_send, error::permission_denied(E_NOT_AUTHORIZED));
        assert!(!exists<UsernameRegistry>(@aptos_send), error::already_exists(E_USERNAME_ALREADY_EXISTS));
        
        move_to(admin, UsernameRegistry {
            username_to_address: table::new(),
            address_to_username: table::new(),
            username_registered_events: account::new_event_handle<UsernameRegisteredEvent>(admin),
            username_updated_events: account::new_event_handle<UsernameUpdatedEvent>(admin),
        });
    }

    /// Register a username for the caller
    public entry fun register_username(user: &signer, username: String) acquires UsernameRegistry {
        let user_addr = signer::address_of(user);
        
        // Validate username (basic validation - can be expanded)
        assert!(string::length(&username) > 0 && string::length(&username) <= 32, error::invalid_argument(E_INVALID_USERNAME));
        
        // Initialize registry if it doesn't exist (only if caller is the module owner)
        if (!exists<UsernameRegistry>(@aptos_send)) {
            assert!(user_addr == @aptos_send, error::permission_denied(E_NOT_AUTHORIZED));
            
            move_to(user, UsernameRegistry {
                username_to_address: table::new(),
                address_to_username: table::new(),
                username_registered_events: account::new_event_handle<UsernameRegisteredEvent>(user),
                username_updated_events: account::new_event_handle<UsernameUpdatedEvent>(user),
            });
        };
        
        let registry = borrow_global_mut<UsernameRegistry>(@aptos_send);
        
        // Check if username already exists
        assert!(!table::contains(&registry.username_to_address, username), error::already_exists(E_USERNAME_ALREADY_EXISTS));
        
        // If user already has a username, remove the old mapping
        if (table::contains(&registry.address_to_username, user_addr)) {
            let old_username = table::remove(&mut registry.address_to_username, user_addr);
            table::remove(&mut registry.username_to_address, old_username);
        };
        
        // Add new mappings
        table::add(&mut registry.username_to_address, username, user_addr);
        table::add(&mut registry.address_to_username, user_addr, username);
        
        // Emit event
        event::emit_event(&mut registry.username_registered_events, UsernameRegisteredEvent {
            username,
            user_address: user_addr,
        });
    }

    /// Update username for the caller
    public entry fun update_username(user: &signer, new_username: String) acquires UsernameRegistry {
        let user_addr = signer::address_of(user);
        
        // Validate username
        assert!(string::length(&new_username) > 0 && string::length(&new_username) <= 32, error::invalid_argument(E_INVALID_USERNAME));
        
        let registry = borrow_global_mut<UsernameRegistry>(@aptos_send);
        
        // Check if new username already exists
        assert!(!table::contains(&registry.username_to_address, new_username), error::already_exists(E_USERNAME_ALREADY_EXISTS));
        
        // Check if user has an existing username
        assert!(table::contains(&registry.address_to_username, user_addr), error::not_found(E_USERNAME_NOT_FOUND));
        
        // Get old username and remove old mappings
        let old_username = table::remove(&mut registry.address_to_username, user_addr);
        table::remove(&mut registry.username_to_address, old_username);
        
        // Add new mappings
        table::add(&mut registry.username_to_address, new_username, user_addr);
        table::add(&mut registry.address_to_username, user_addr, new_username);
        
        // Emit event
        event::emit_event(&mut registry.username_updated_events, UsernameUpdatedEvent {
            old_username,
            new_username,
            user_address: user_addr,
        });
    }

    /// Get address by username
    #[view]
    public fun get_address_by_username(username: String): address acquires UsernameRegistry {
        let registry = borrow_global<UsernameRegistry>(@aptos_send);
        assert!(table::contains(&registry.username_to_address, username), error::not_found(E_USERNAME_NOT_FOUND));
        *table::borrow(&registry.username_to_address, username)
    }

    /// Get username by address
    #[view]
    public fun get_username_by_address(addr: address): String acquires UsernameRegistry {
        let registry = borrow_global<UsernameRegistry>(@aptos_send);
        assert!(table::contains(&registry.address_to_username, addr), error::not_found(E_USERNAME_NOT_FOUND));
        *table::borrow(&registry.address_to_username, addr)
    }

    /// Check if username exists
    #[view]
    public fun username_exists(username: String): bool acquires UsernameRegistry {
        let registry = borrow_global<UsernameRegistry>(@aptos_send);
        table::contains(&registry.username_to_address, username)
    }

    /// Check if address has username
    #[view]
    public fun address_has_username(addr: address): bool acquires UsernameRegistry {
        let registry = borrow_global<UsernameRegistry>(@aptos_send);
        table::contains(&registry.address_to_username, addr)
    }
}
