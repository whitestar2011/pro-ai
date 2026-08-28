import sqlite3

DB = 'users_v2.db'

conn = sqlite3.connect(DB)
c = conn.cursor()

c.execute("SELECT id, email, username, is_verified, incognito FROM users ORDER BY id DESC")
users = c.fetchall()

print("="*60)
print(f"{'ID':<5} {'EMAIL':<30} {'USERNAME':<15} {'VERIFIED':<10} {'INCOGNITO'}")
print("="*60)

for u in users:
    verified = "Yes" if u[3] == 1 else "No"
    incog = "ON" if u[4] == 1 else "OFF"
    print(f"{u[0]:<5} {u[1]:<30} {str(u[2]):<15} {verified:<10} {incog}")

print("="*60)
print(f"Total Users: {len(users)}")
conn.close()
