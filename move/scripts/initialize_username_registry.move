script {
    use aptos_send::username_registry;

    fun initialize_username_registry(admin: &signer) {
        username_registry::initialize(admin);
    }
}
