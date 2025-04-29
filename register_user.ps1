$username = "admin"
$email = "admin@example.com"
$password = "admin123"

$body = @{
    username = $username
    email = $email
    password = $password
} | ConvertTo-Json

Write-Host "Creating new user with username: $username and email: $email"

# Send the registration request
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users/" -Method Post -Body $body -ContentType "application/json" -ErrorAction SilentlyContinue

if ($response) {
    Write-Host "User registered successfully!"
    Write-Host "You can now log in with:"
    Write-Host "Username: $username"
    Write-Host "Password: $password"
} else {
    Write-Host "Failed to register user. The user might already exist or the server is not running."
}