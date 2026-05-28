path "secret/data/fishmap/external/mapbox" {
  capabilities = ["read"]
}

path "secret/data/fishmap/database/postgres" {
  capabilities = ["read"]
}

path "secret/data/fishmap/auth/jwt" {
  capabilities = ["read"]
}
