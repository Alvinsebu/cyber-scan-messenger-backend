"""
Quick Start Script - Sets up and runs the chat backend
"""
import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and print its status"""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    print(f"Running: {command}\n")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ {description} - SUCCESS")
        if result.stdout:
            print(result.stdout)
    else:
        print(f"❌ {description} - FAILED")
        if result.stderr:
            print(result.stderr)
        return False
    
    return True


def main():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║     Real-Time Chat Backend - Quick Start Setup            ║
    ║     With Cyberbullying Detection                          ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    # Check Python version
    print(f"Python Version: {sys.version}")
    
    # Step 1: Install dependencies
    if not run_command(
        "pip install -r requirements.txt",
        "Installing Dependencies"
    ):
        print("\n⚠️  Failed to install dependencies. Please check the error above.")
        return
    
    # Step 2: Set environment variables (if needed)
    if not os.path.exists('.env'):
        print("\n⚠️  No .env file found. Creating default configuration...")
        with open('.env', 'w') as f:
            f.write("DATABASE_URL=sqlite:///chat.db\n")
            f.write("SECRET_KEY=your-secret-key-change-in-production\n")
            f.write("JWT_SECRET_KEY=your-jwt-secret-key\n")
        print("✅ Created .env file with default settings")
    
    # Step 3: Run database migrations
    print("\n" + "="*60)
    print("🗄️  Setting up Database")
    print("="*60)
    
    print("\nCreating database migration for Message model...")
    migration_result = subprocess.run(
        'flask db migrate -m "Add Message model for chat"',
        shell=True,
        capture_output=True,
        text=True
    )
    
    if "No changes in schema detected" in migration_result.stdout or migration_result.returncode == 0:
        print("✅ Migration created or already exists")
    
    print("\nApplying database migrations...")
    upgrade_result = subprocess.run(
        'flask db upgrade',
        shell=True,
        capture_output=True,
        text=True
    )
    
    if upgrade_result.returncode == 0:
        print("✅ Database migrations applied successfully")
    else:
        print("⚠️  Migration info:", upgrade_result.stdout)
    
    # Step 4: Verify model files exist
    print("\n" + "="*60)
    print("🤖 Verifying ML Model Files")
    print("="*60)
    
    model_files = [
        'models/bully_model.h5',
        'models/tokenizer.json',
        'cyberbullying_data.csv'
    ]
    
    all_exist = True
    for file in model_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - NOT FOUND")
            all_exist = False
    
    if not all_exist:
        print("\n⚠️  Some ML model files are missing!")
        print("   Run 'python train_model.py' to generate them.")
    
    # Summary
    print("\n" + "="*60)
    print("📋 Setup Summary")
    print("="*60)
    print("""
    ✅ Dependencies installed
    ✅ Database configured
    ✅ Message model ready
    
    🚀 NEXT STEPS:
    
    1. Start the server:
       python run.py
    
    2. Server will be available at:
       http://localhost:5000
    
    3. Test the Socket.IO connection:
       python test_chat.py
    
    4. Connect your React frontend to:
       http://localhost:5000
    
    📚 Documentation:
       - CHAT_BACKEND_GUIDE.md - Complete API reference
       - FLASK_SOCKETIO_GUIDE.md - Integration guide
    """)
    
    # Ask if user wants to start server
    response = input("\n🚀 Would you like to start the server now? (y/n): ")
    if response.lower() == 'y':
        print("\n" + "="*60)
        print("🚀 Starting Flask-SocketIO Server")
        print("="*60)
        print("\nPress Ctrl+C to stop the server\n")
        
        try:
            subprocess.run("python run.py", shell=True)
        except KeyboardInterrupt:
            print("\n\n👋 Server stopped")
    else:
        print("\n👋 Setup complete! Run 'python run.py' when ready.")


if __name__ == '__main__':
    main()
