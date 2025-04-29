$username = "admin"
$email = "admin@example.com"
$password = "admin123"

# Import the bcrypt module from Python to hash the password correctly
$hash_script = @"
import bcrypt
import uuid
from datetime import datetime

# Generate password hash the same way the app does
def get_password_hash(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

# Create a unique ID
user_id = str(uuid.uuid4())
hashed_password = get_password_hash('$password')
now = datetime.utcnow().isoformat()

# Output the values for SQLite
print(f"{user_id}|{hashed_password}|{now}")
"@

# Save to a temporary Python script
$tempFile = [System.IO.Path]::GetTempFileName() + ".py"
$hash_script | Out-File -FilePath $tempFile -Encoding UTF8

Write-Host "Generating password hash and user ID..."
# Activate the virtual environment and run the Python script
$pythonOutput = & "d:\SENG\691\Project\AI-Powered Learning Companion\backend\venv-311\Scripts\python.exe" $tempFile
$values = $pythonOutput -split '\|'
$user_id = $values[0]
$hashed_password = $values[1]
$timestamp = $values[2]

# Create SQL command to insert the user
$sql = @"
INSERT INTO users (id, username, email, hashed_password, created_at, updated_at, is_active, is_superuser)
VALUES ('$user_id', '$username', '$email', '$hashed_password', '$timestamp', '$timestamp', 1, 1);
"@

Write-Host "Adding user to database..."
# Execute the SQL command
$dbPath = "d:\SENG\691\Project\AI-Powered Learning Companion\backend\learning_companion.db"
# Check if sqlite3 is in PATH or use the full path if you know where it is
$sqliteCommand = "sqlite3 `"$dbPath`" `"$sql`""

# Execute the command
try {
    Invoke-Expression $sqliteCommand
    Write-Host "User created successfully!"
    Write-Host "You can now log in with:"
    Write-Host "Username: $username"
    Write-Host "Password: $password"
} catch {
    Write-Host "Error creating user: $_"
    Write-Host "You may need to install SQLite or make sure it's in your PATH"
}

# Clean up
Remove-Item $tempFile