UPDATE users SET password_hash = '$2b$12$IJQHAYZrapnSLHgxl2uYNu4Cm8U8o00wrCZfHf2utCn1VsYL/Vpbu' WHERE email = 'test@example.com';
SELECT email, length(password_hash) as hash_length, substring(password_hash, 1, 60) as hash_prefix FROM users WHERE email = 'test@example.com';
