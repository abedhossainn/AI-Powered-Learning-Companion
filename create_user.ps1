# PowerShell script to create an admin user for the AI-Powered Learning Companion application
Write-Host "Creating admin user for AI-Powered Learning Companion" -ForegroundColor Green

$baseUrl = "http://localhost:8000"
$apiUrl = "$baseUrl/api/v1"

# Admin user credentials
$username = "admin"
$email = "admin@example.com"
$password = "admin123"

# Create the user
$userData = @{
    username = $username
    email = $email
    password = $password
} | ConvertTo-Json

Write-Host "Creating admin user..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$apiUrl/users/" -Method Post -Body $userData -ContentType "application/json"
    Write-Host "User created successfully!" -ForegroundColor Green
    Write-Host "`nYou can now log in with:" -ForegroundColor Green
    Write-Host "Username: $username" -ForegroundColor Green
    Write-Host "Password: $password" -ForegroundColor Green
} catch {
    $errorDetails = $_.ErrorDetails.Message
    if ($errorDetails -match "Email already registered|Username already taken") {
        Write-Host "User already exists! You can log in with:" -ForegroundColor Yellow
        Write-Host "Username: $username" -ForegroundColor Yellow
        Write-Host "Password: $password" -ForegroundColor Yellow
    } else {
        Write-Host "Failed to create user: $_" -ForegroundColor Red
    }
}

# Verify login works
Write-Host "`nVerifying login credentials..." -ForegroundColor Cyan

$formData = [ordered]@{
    "username" = $username
    "password" = $password
}

try {
    $response = Invoke-RestMethod -Uri "$apiUrl/users/token" -Method Post -Form $formData
    Write-Host "Login successful! Your access token is valid." -ForegroundColor Green
} catch {
    Write-Host "Login failed: $_" -ForegroundColor Red
}