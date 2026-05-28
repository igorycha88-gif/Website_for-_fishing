path "secret/data/fishmap/payment/*" {
  capabilities = ["read"]
}

path "secret/data/fishmap/database/postgres" {
  capabilities = ["read"]
}

path "secret/data/fishmap/auth/jwt" {
  capabilities = ["read"]
}
