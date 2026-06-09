UPDATE users SET password_hash = '$pbkdf2-sha256$29000$LcUYQ2itlVLKubcWgnAuBQ$5zYCd43Bts4ha0ZlJJYU88uh1Xci07pK5YXd0xVg9qg' WHERE email = 'test@example.com';
SELECT email, length(password_hash) as hash_length FROM users WHERE email = 'test@example.com';
