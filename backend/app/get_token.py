from supabase import create_client



supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

email = "anish@gmail.com"
password = "test123"

res = supabase.auth.sign_in_with_password({
    "email": email,
    "password": password
})

print("ACCESS TOKEN:\n")
print(res.session.access_token)