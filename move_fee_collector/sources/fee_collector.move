module fee_collector::fee_collector {
    use std::string::{Self, String};
    use std::signer;
    use std::error;
    use aptos_std::table::{Self, Table};
    use aptos_framework::account;
    use aptos_framework::event::{Self, EventHandle};
    use aptos_framework::coin;
    use aptos_framework::aptos_coin::AptosCoin;

    /// Error codes
    const E_FEE_COLLECTOR_NOT_INITIALIZED: u64 = 1;
    const E_INVALID_FEE_PERCENTAGE: u64 = 2;
    const E_NOT_ADMIN: u64 = 3;
    const E_INSUFFICIENT_FUNDS: u64 = 4;

    /// Transaction type constants
    const TRANSACTION_TYPE_P2P_DOMESTIC: u8 = 1;
    const TRANSACTION_TYPE_P2P_CROSS_BORDER: u8 = 2;
    const TRANSACTION_TYPE_CARD_PRESENT: u8 = 3;
    const TRANSACTION_TYPE_CARD_NOT_PRESENT: u8 = 4;
    const TRANSACTION_TYPE_MERCHANT: u8 = 5;

    /// Fee percentage constants (in basis points, e.g., 25 = 0.25%)
    const FEE_P2P_DOMESTIC: u64 = 25;  // 0.25%
    const FEE_P2P_CROSS_BORDER: u64 = 50;  // 0.5%
    const FEE_CARD_PRESENT: u64 = 180;  // 1.8%
    const FEE_CARD_NOT_PRESENT: u64 = 250;  // 2.5%
    const FEE_MERCHANT: u64 = 150;  // 1.5%

    /// Fee collector resource
    struct FeeCollector has key {
        /// Maps currency type to collected fees
        collected_fees: Table<String, u64>,
        /// Admin address for fee management
        admin: address,
        /// Fee configuration
        fee_config: Table<u8, u64>, // transaction_type -> fee_percentage
        /// Event handles
        fee_collected_events: EventHandle<FeeCollectedEvent>,
        fee_withdrawn_events: EventHandle<FeeWithdrawnEvent>,
    }

    /// Events
    struct FeeCollectedEvent has drop, store {
        transaction_id: String,
        payer: address,
        fee_amount: u64,
        currency_type: String,
        transaction_type: u8,
    }

    struct FeeWithdrawnEvent has drop, store {
        admin: address,
        amount: u64,
        currency_type: String,
        destination_address: address,
    }

    /// Initialize the fee collector (called once by admin)
    public entry fun initialize(admin: &signer) acquires FeeCollector {
        let admin_addr = signer::address_of(admin);
        assert!(!exists<FeeCollector>(@fee_collector), error::already_exists(E_FEE_COLLECTOR_NOT_INITIALIZED));
        
        // Initialize fee collector
        move_to(admin, FeeCollector {
            collected_fees: table::new(),
            admin: admin_addr,
            fee_config: table::new(),
            fee_collected_events: account::new_event_handle<FeeCollectedEvent>(admin),
            fee_withdrawn_events: account::new_event_handle<FeeWithdrawnEvent>(admin),
        });
        
        // Initialize fee configuration
        initialize_fee_config(admin);
    }
    
    /// Initialize fee configuration (internal function)
    fun initialize_fee_config(_admin: &signer) acquires FeeCollector {
        let fee_collector = borrow_global_mut<FeeCollector>(@fee_collector);
        table::add(&mut fee_collector.fee_config, TRANSACTION_TYPE_P2P_DOMESTIC, FEE_P2P_DOMESTIC);
        table::add(&mut fee_collector.fee_config, TRANSACTION_TYPE_P2P_CROSS_BORDER, FEE_P2P_CROSS_BORDER);
        table::add(&mut fee_collector.fee_config, TRANSACTION_TYPE_CARD_PRESENT, FEE_CARD_PRESENT);
        table::add(&mut fee_collector.fee_config, TRANSACTION_TYPE_CARD_NOT_PRESENT, FEE_CARD_NOT_PRESENT);
        table::add(&mut fee_collector.fee_config, TRANSACTION_TYPE_MERCHANT, FEE_MERCHANT);
    }

    /// Collect fees from a transaction (called by payment system)
    public entry fun collect_fee(
        payer: &signer,
        transaction_id: String,
        fee_amount: u64,
        currency_type: String,
        transaction_type: u8
    ) acquires FeeCollector {
        let payer_addr = signer::address_of(payer);
        assert!(exists<FeeCollector>(@fee_collector), error::not_found(E_FEE_COLLECTOR_NOT_INITIALIZED));
        
        let fee_collector = borrow_global_mut<FeeCollector>(@fee_collector);
        
        // For APT fees, transfer the coins to the fee collector
        if (currency_type == string::utf8(b"APT")) {
            let fee_payment = coin::withdraw<AptosCoin>(payer, fee_amount);
            coin::deposit(@fee_collector, fee_payment);
        };
        
        // Update collected fees
        if (table::contains(&fee_collector.collected_fees, currency_type)) {
            let current_fees = table::borrow_mut(&mut fee_collector.collected_fees, currency_type);
            *current_fees = *current_fees + fee_amount;
        } else {
            table::add(&mut fee_collector.collected_fees, currency_type, fee_amount);
        };
        
        // Emit fee collected event
        event::emit_event(&mut fee_collector.fee_collected_events, FeeCollectedEvent {
            transaction_id,
            payer: payer_addr,
            fee_amount,
            currency_type,
            transaction_type,
        });
    }

    /// Withdraw collected fees (admin only)
    public entry fun withdraw_fees(
        admin: &signer,
        currency_type: String,
        amount: u64,
        destination_address: address
    ) acquires FeeCollector {
        let admin_addr = signer::address_of(admin);
        assert!(exists<FeeCollector>(@fee_collector), error::not_found(E_FEE_COLLECTOR_NOT_INITIALIZED));
        
        let fee_collector = borrow_global_mut<FeeCollector>(@fee_collector);
        assert!(fee_collector.admin == admin_addr, error::permission_denied(E_NOT_ADMIN));
        
        // Check if we have enough collected fees
        assert!(table::contains(&fee_collector.collected_fees, currency_type), error::not_found(E_INSUFFICIENT_FUNDS));
        let available_fees = table::borrow(&fee_collector.collected_fees, currency_type);
        assert!(*available_fees >= amount, error::invalid_argument(E_INSUFFICIENT_FUNDS));
        
        // For APT, transfer the coins
        if (currency_type == string::utf8(b"APT")) {
            let withdrawal = coin::withdraw<AptosCoin>(admin, amount);
            coin::deposit(destination_address, withdrawal);
        };
        
        // Update collected fees
        let current_fees = table::borrow_mut(&mut fee_collector.collected_fees, currency_type);
        *current_fees = *current_fees - amount;
        
        // Emit fee withdrawn event
        event::emit_event(&mut fee_collector.fee_withdrawn_events, FeeWithdrawnEvent {
            admin: admin_addr,
            amount,
            currency_type,
            destination_address,
        });
    }

    /// Update fee percentage for a transaction type (admin only)
    public entry fun update_fee_percentage(
        admin: &signer,
        transaction_type: u8,
        new_fee_percentage: u64
    ) acquires FeeCollector {
        let admin_addr = signer::address_of(admin);
        assert!(exists<FeeCollector>(@fee_collector), error::not_found(E_FEE_COLLECTOR_NOT_INITIALIZED));
        
        let fee_collector = borrow_global_mut<FeeCollector>(@fee_collector);
        assert!(fee_collector.admin == admin_addr, error::permission_denied(E_NOT_ADMIN));
        assert!(new_fee_percentage <= 10000, error::invalid_argument(E_INVALID_FEE_PERCENTAGE)); // Max 100%
        
        table::upsert(&mut fee_collector.fee_config, transaction_type, new_fee_percentage);
    }

    /// View functions

    /// Get collected fees for a currency type
    public fun get_collected_fees(currency_type: String): u64 acquires FeeCollector {
        assert!(exists<FeeCollector>(@fee_collector), error::not_found(E_FEE_COLLECTOR_NOT_INITIALIZED));
        let fee_collector = borrow_global<FeeCollector>(@fee_collector);
        if (table::contains(&fee_collector.collected_fees, currency_type)) {
            *table::borrow(&fee_collector.collected_fees, currency_type)
        } else {
            0
        }
    }

    /// Get fee percentage for a transaction type
    public fun get_fee_percentage(transaction_type: u8): u64 acquires FeeCollector {
        assert!(exists<FeeCollector>(@fee_collector), error::not_found(E_FEE_COLLECTOR_NOT_INITIALIZED));
        let fee_collector = borrow_global<FeeCollector>(@fee_collector);
        if (table::contains(&fee_collector.fee_config, transaction_type)) {
            *table::borrow(&fee_collector.fee_config, transaction_type)
        } else {
            0
        }
    }

    /// Calculate fee amount for a given transaction
    public fun calculate_fee(amount: u64, transaction_type: u8): u64 acquires FeeCollector {
        let fee_percentage = get_fee_percentage(transaction_type);
        (amount * fee_percentage) / 10000 // Convert basis points to percentage
    }

    /// Check if fee collector is initialized
    public fun is_initialized(): bool {
        exists<FeeCollector>(@fee_collector)
    }

    /// Get admin address
    public fun get_admin(): address acquires FeeCollector {
        assert!(exists<FeeCollector>(@fee_collector), error::not_found(E_FEE_COLLECTOR_NOT_INITIALIZED));
        let fee_collector = borrow_global<FeeCollector>(@fee_collector);
        fee_collector.admin
    }
}
