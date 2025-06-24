CREATE TABLE users (
	user_id SERIAL PRIMARY KEY,
	username TEXT UNIQUE NOT NULL,
	password_hash TEXT NOT NULL,
	email TEXT UNIQUE NOT NULL,
	reset_token TEXT,
	role TEXT DEFAULT 'user', -- 'admin' or 'user'
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE warranty_items (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL,
  item_name VARCHAR(100) NOT NULL,
  category VARCHAR(50) NOT NULL,
  purchase_date DATE NOT NULL,
  warranty_end_date DATE NOT NULL,
  warranty_card_image BYTEA NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

INSERT INTO users (username,password_hash,email,role) VALUES (
  'admin',
  'hash_from_gethash.py',
  'your_mail',
  'admin'
);
