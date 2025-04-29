# PowerShell script to create a user with curl
Write-Host "Creating admin user for AI-Powered Learning Companion" -ForegroundColor Green

$json = @"
{
    "username": "admin",
    "email": "admin@example.com",
    "password": "admin123"
}
"@

Write-Host "Creating user with username: admin, password: admin123"
curl -X POST http://localhost:8000/api/v1/users/ -H "Content-Type: application/json" -d $json

Write-Host "`nYou can now log in with:"
Write-Host "Username: admin"
Write-Host "Password: admin123"