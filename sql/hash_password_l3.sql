CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE FUNCTION hash_password(plain_password TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN crypt(plain_password, gen_salt('bf', 12));
END;
$$ LANGUAGE plpgsql;