# Database Configuration
import os

# Supabase Configuration
SUPABASE_URL = "https://uoqyboiftoonhudqosxb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVvcXlib2lmdG9vbmh1ZHFvc3hiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ2MzA2ODksImV4cCI6MjA3MDIwNjY4OX0.AZmflgGF-RDuND_IDn68HkiM1zrVhnDEVsT53j3sMFo"

# Database table name
DB_TABLE = "materials_stage"

# Set environment variables for the fabric matcher
os.environ["SUPABASE_URL"] = SUPABASE_URL
os.environ["SUPABASE_KEY"] = SUPABASE_KEY
os.environ["DB_TABLE"] = DB_TABLE
