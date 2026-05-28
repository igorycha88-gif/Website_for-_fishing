path "secret/data/fishmap/storage/*" {
  capabilities = ["read"]
}

path "secret/data/fishmap/database/postgres" {
  capabilities = ["read"]
}
