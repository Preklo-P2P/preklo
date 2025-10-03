module aptos_send::payment_forwarding {
    use std::string::{Self, String};
    use std::signer;
    use std::error;
    use aptos_std::table::{Self, Table};
    use aptos_framework::account;
    use aptos_framework::event::{Self, EventHandle};
    use aptos_framework::coin;
    use aptos_framework::aptos_coin::AptosCoin;
    use aptos_framework::timestamp;

    /// Error codes
    const E_PAYMENT_REQUEST_NOT_FOUND: u64 = 1;
    const E_PAYMENT_REQUEST_EXPIRED: u64 = 2;
    const E_PAYMENT_REQUEST_ALREADY_PAID: u64 = 3;
    const E_INSUFFICIENT_AMOUNT: u64 = 4;
    const E_NOT_AUTHORIZED: u64 = 5;
    const E_FEE_COLLECTOR_NOT_INITIALIZED: u64 = 6;
    const E_INVALID_FEE_PERCENTAGE: u64 = 7;
    const E_NOT_ADMIN: u64 = 8;

    /// Payment request status
    const PAYMENT_STATUS_PENDING: u8 = 0;
    const PAYMENT_STATUS_PAID: u8 = 1;
    const PAYMENT_STATUS_EXPIRED: u8 = 2;
    const PAYMENT_STATUS_CANCELLED: u8 = 3;

    /// Transaction types for fee calculation
    const TRANSACTION_TYPE_P2P_DOMESTIC: u8 = 0;
    const TRANSACTION_TYPE_P2P_CROSS_BORDER: u8 = 1;
    const TRANSACTION_TYPE_CARD_PRESENT: u8 = 2;
    const TRANSACTION_TYPE_CARD_NOT_PRESENT: u8 = 3;
    const TRANSACTION_TYPE_MERCHANT: u8 = 4;

    /// Fee percentages (in basis points, e.g., 25 = 0.25%)
    const FEE_P2P_DOMESTIC: u64 = 25;        // 0.25%
    const FEE_P2P_CROSS_BORDER: u64 = 50;    // 0.5%
    const FEE_CARD_PRESENT: u64 = 180;       // 1.8%
    const FEE_CARD_NOT_PRESENT: u64 = 250;   // 2.5%
    const FEE_MERCHANT: u64 = 150;           // 1.5%

    /// Payment request structure
    struct PaymentRequest has store {
        recipient: address,
        amount: u64,
        currency_type: String, // e.g., "USDC", "APT"
        description: String,
        expiry_timestamp: u64,
        status: u8,
        created_timestamp: u64,
        transaction_type: u8, // For fee calculation
        fee_amount: u64,      // Calculated fee amount
    }

    /// Fee collector resource for collecting transaction fees
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

    /// Payment registry resource
    struct PaymentRegistry has key {
        /// Maps payment ID to payment request
        payment_requests: Table<String, PaymentRequest>,
        /// Event handles
        payment_request_created_events: EventHandle<PaymentRequestCreatedEvent>,
        payment_completed_events: EventHandle<PaymentCompletedEvent>,
        payment_cancelled_events: EventHandle<PaymentCancelledEvent>,
    }

    /// Events
    struct PaymentRequestCreatedEvent has drop, store {
        payment_id: String,
        recipient: address,
        amount: u64,
        currency_type: String,
        description: String,
        expiry_timestamp: u64,
    }

    struct PaymentCompletedEvent has drop, store {
        payment_id: String,
        payer: address,
        recipient: address,
        amount: u64,
        currency_type: String,
    }

    struct PaymentCancelledEvent has drop, store {
        payment_id: String,
        recipient: address,
    }

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
    }

    /// Initialize the payment registry and fee collector (called once by admin)
    public entry fun initialize(admin: &signer) acquires FeeCollector {
        let admin_addr = signer::address_of(admin);
        assert!(!exists<PaymentRegistry>(admin_addr), error::already_exists(E_PAYMENT_REQUEST_NOT_FOUND));
        assert!(!exists<FeeCollector>(@aptos_send), error::already_exists(E_FEE_COLLECTOR_NOT_INITIALIZED));
        
        // Initialize payment registry
        move_to(admin, PaymentRegistry {
            payment_requests: table::new(),
            payment_request_created_events: account::new_event_handle<PaymentRequestCreatedEvent>(admin),
            payment_completed_events: account::new_event_handle<PaymentCompletedEvent>(admin),
            payment_cancelled_events: account::new_event_handle<PaymentCancelledEvent>(admin),
        });

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
        let fee_collector = borrow_global_mut<FeeCollector>(@aptos_send);
        table::add(&mut fee_collector.fee_config, TRANSACTION_TYPE_P2P_DOMESTIC, FEE_P2P_DOMESTIC);
        table::add(&mut fee_collector.fee_config, TRANSACTION_TYPE_P2P_CROSS_BORDER, FEE_P2P_CROSS_BORDER);
        table::add(&mut fee_collector.fee_config, TRANSACTION_TYPE_CARD_PRESENT, FEE_CARD_PRESENT);
        table::add(&mut fee_collector.fee_config, TRANSACTION_TYPE_CARD_NOT_PRESENT, FEE_CARD_NOT_PRESENT);
        table::add(&mut fee_collector.fee_config, TRANSACTION_TYPE_MERCHANT, FEE_MERCHANT);
    }

    /// Create a payment request with transaction type for fee calculation
    public entry fun create_payment_request(
        recipient: &signer,
        payment_id: String,
        amount: u64,
        currency_type: String,
        description: String,
        expiry_hours: u64,
        transaction_type: u8
    ) acquires PaymentRegistry, FeeCollector {
        let recipient_addr = signer::address_of(recipient);
        let current_time = timestamp::now_seconds();
        let expiry_timestamp = current_time + (expiry_hours * 3600); // Convert hours to seconds
        
        let registry = borrow_global_mut<PaymentRegistry>(@aptos_send);
        let fee_collector = borrow_global<FeeCollector>(@aptos_send);
        
        // Check if payment ID already exists
        assert!(!table::contains(&registry.payment_requests, payment_id), error::already_exists(E_PAYMENT_REQUEST_NOT_FOUND));
        
        // Calculate fee amount
        let fee_percentage = *table::borrow(&fee_collector.fee_config, transaction_type);
        let fee_amount = (amount * fee_percentage) / 10000; // Convert basis points to percentage
        
        let payment_request = PaymentRequest {
            recipient: recipient_addr,
            amount,
            currency_type,
            description,
            expiry_timestamp,
            status: PAYMENT_STATUS_PENDING,
            created_timestamp: current_time,
            transaction_type,
            fee_amount,
        };
        
        table::add(&mut registry.payment_requests, payment_id, payment_request);
        
        // Emit event
        event::emit_event(&mut registry.payment_request_created_events, PaymentRequestCreatedEvent {
            payment_id,
            recipient: recipient_addr,
            amount,
            currency_type,
            description,
            expiry_timestamp,
        });
    }

    /// Pay a payment request with APT and collect fees
    public entry fun pay_with_apt(
        payer: &signer,
        payment_id: String
    ) acquires PaymentRegistry, FeeCollector {
        let payer_addr = signer::address_of(payer);
        let registry = borrow_global_mut<PaymentRegistry>(@aptos_send);
        let fee_collector = borrow_global_mut<FeeCollector>(@aptos_send);
        
        // Check if payment request exists
        assert!(table::contains(&registry.payment_requests, payment_id), error::not_found(E_PAYMENT_REQUEST_NOT_FOUND));
        
        let payment_request = table::borrow_mut(&mut registry.payment_requests, payment_id);
        
        // Check if payment is still pending
        assert!(payment_request.status == PAYMENT_STATUS_PENDING, error::invalid_state(E_PAYMENT_REQUEST_ALREADY_PAID));
        
        // Check if payment hasn't expired
        let current_time = timestamp::now_seconds();
        assert!(current_time <= payment_request.expiry_timestamp, error::invalid_state(E_PAYMENT_REQUEST_EXPIRED));
        
        // For APT payments, transfer the coins with fee collection
        if (payment_request.currency_type == string::utf8(b"APT")) {
            let total_amount = payment_request.amount + payment_request.fee_amount;
            let total_payment = coin::withdraw<AptosCoin>(payer, total_amount);
            
            // Split payment: net amount to recipient, fee to fee collector
            let net_amount = payment_request.amount;
            let fee_amount = payment_request.fee_amount;
            
            // Transfer net amount to recipient
            let recipient_payment = coin::extract(&mut total_payment, net_amount);
            coin::deposit(payment_request.recipient, recipient_payment);
            
            // Transfer fee to fee collector
            coin::deposit(@aptos_send, total_payment);
            
            // Update collected fees
            if (table::contains(&fee_collector.collected_fees, payment_request.currency_type)) {
                let current_fees = table::borrow_mut(&mut fee_collector.collected_fees, payment_request.currency_type);
                *current_fees = *current_fees + fee_amount;
            } else {
                table::add(&mut fee_collector.collected_fees, payment_request.currency_type, fee_amount);
            };
            
            // Emit fee collected event
            event::emit_event(&mut fee_collector.fee_collected_events, FeeCollectedEvent {
                transaction_id: payment_id,
                payer: payer_addr,
                fee_amount,
                currency_type: payment_request.currency_type,
                transaction_type: payment_request.transaction_type,
            });
        };
        
        // Update payment status
        payment_request.status = PAYMENT_STATUS_PAID;
        
        // Emit event
        event::emit_event(&mut registry.payment_completed_events, PaymentCompletedEvent {
            payment_id,
            payer: payer_addr,
            recipient: payment_request.recipient,
            amount: payment_request.amount,
            currency_type: payment_request.currency_type,
        });
    }

    /// Cancel a payment request (only by recipient)
    public entry fun cancel_payment_request(
        recipient: &signer,
        payment_id: String
    ) acquires PaymentRegistry {
        let recipient_addr = signer::address_of(recipient);
        let registry = borrow_global_mut<PaymentRegistry>(@aptos_send);
        
        // Check if payment request exists
        assert!(table::contains(&registry.payment_requests, payment_id), error::not_found(E_PAYMENT_REQUEST_NOT_FOUND));
        
        let payment_request = table::borrow_mut(&mut registry.payment_requests, payment_id);
        
        // Check if caller is the recipient
        assert!(payment_request.recipient == recipient_addr, error::permission_denied(E_NOT_AUTHORIZED));
        
        // Check if payment is still pending
        assert!(payment_request.status == PAYMENT_STATUS_PENDING, error::invalid_state(E_PAYMENT_REQUEST_ALREADY_PAID));
        
        // Update payment status
        payment_request.status = PAYMENT_STATUS_CANCELLED;
        
        // Emit event
        event::emit_event(&mut registry.payment_cancelled_events, PaymentCancelledEvent {
            payment_id,
            recipient: recipient_addr,
        });
    }

    /// Get payment request details
    #[view]
    public fun get_payment_request(payment_id: String): (address, u64, String, String, u64, u8, u64) acquires PaymentRegistry {
        let registry = borrow_global<PaymentRegistry>(@aptos_send);
        assert!(table::contains(&registry.payment_requests, payment_id), error::not_found(E_PAYMENT_REQUEST_NOT_FOUND));
        
        let payment_request = table::borrow(&registry.payment_requests, payment_id);
        (
            payment_request.recipient,
            payment_request.amount,
            payment_request.currency_type,
            payment_request.description,
            payment_request.expiry_timestamp,
            payment_request.status,
            payment_request.created_timestamp
        )
    }

    /// Check if payment request exists
    #[view]
    public fun payment_request_exists(payment_id: String): bool acquires PaymentRegistry {
        let registry = borrow_global<PaymentRegistry>(@aptos_send);
        table::contains(&registry.payment_requests, payment_id)
    }

    /// Get payment status
    #[view]
    public fun get_payment_status(payment_id: String): u8 acquires PaymentRegistry {
        let registry = borrow_global<PaymentRegistry>(@aptos_send);
        assert!(table::contains(&registry.payment_requests, payment_id), error::not_found(E_PAYMENT_REQUEST_NOT_FOUND));
        
        let payment_request = table::borrow(&registry.payment_requests, payment_id);
        payment_request.status
    }

    /// Withdraw collected fees (admin only)
    public entry fun withdraw_fees(
        admin: &signer,
        currency_type: String,
        amount: u64
    ) acquires FeeCollector {
        let admin_addr = signer::address_of(admin);
        let fee_collector = borrow_global_mut<FeeCollector>(@aptos_send);
        
        // Check if caller is admin
        assert!(fee_collector.admin == admin_addr, error::permission_denied(E_NOT_ADMIN));
        
        // Check if there are enough collected fees
        assert!(table::contains(&fee_collector.collected_fees, currency_type), error::not_found(E_PAYMENT_REQUEST_NOT_FOUND));
        
        let collected_amount = table::borrow_mut(&mut fee_collector.collected_fees, currency_type);
        assert!(*collected_amount >= amount, error::invalid_argument(E_INSUFFICIENT_AMOUNT));
        
        // Update collected fees
        *collected_amount = *collected_amount - amount;
        
        // For APT, transfer the coins to admin
        if (currency_type == string::utf8(b"APT")) {
            let fee_coins = coin::withdraw<AptosCoin>(admin, amount);
            coin::deposit(admin_addr, fee_coins);
        };
        
        // Emit fee withdrawn event
        event::emit_event(&mut fee_collector.fee_withdrawn_events, FeeWithdrawnEvent {
            admin: admin_addr,
            amount,
            currency_type,
        });
    }

    /// Get collected fees for a currency type
    #[view]
    public fun get_collected_fees(currency_type: String): u64 acquires FeeCollector {
        let fee_collector = borrow_global<FeeCollector>(@aptos_send);
        if (table::contains(&fee_collector.collected_fees, currency_type)) {
            *table::borrow(&fee_collector.collected_fees, currency_type)
        } else {
            0
        }
    }

    /// Get fee percentage for a transaction type
    #[view]
    public fun get_fee_percentage(transaction_type: u8): u64 acquires FeeCollector {
        let fee_collector = borrow_global<FeeCollector>(@aptos_send);
        *table::borrow(&fee_collector.fee_config, transaction_type)
    }

    /// Update fee percentage for a transaction type (admin only)
    public entry fun update_fee_percentage(
        admin: &signer,
        transaction_type: u8,
        new_fee_percentage: u64
    ) acquires FeeCollector {
        let admin_addr = signer::address_of(admin);
        let fee_collector = borrow_global_mut<FeeCollector>(@aptos_send);
        
        // Check if caller is admin
        assert!(fee_collector.admin == admin_addr, error::permission_denied(E_NOT_ADMIN));
        
        // Validate fee percentage (max 10% = 1000 basis points)
        assert!(new_fee_percentage <= 1000, error::invalid_argument(E_INVALID_FEE_PERCENTAGE));
        
        // Update fee configuration
        let fee_config = table::borrow_mut(&mut fee_collector.fee_config, transaction_type);
        *fee_config = new_fee_percentage;
    }

    /// Calculate fee amount for a given transaction
    #[view]
    public fun calculate_fee(amount: u64, transaction_type: u8): u64 acquires FeeCollector {
        let fee_collector = borrow_global<FeeCollector>(@aptos_send);
        let fee_percentage = *table::borrow(&fee_collector.fee_config, transaction_type);
        (amount * fee_percentage) / 10000
    }
}
