from django.contrib.auth import login, authenticate, logout , get_user_model
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomAuthenticationForm , ContactForm
from .models import Product , ContactMessage
from django.core.mail import send_mail , BadHeaderError , EmailMessage
import random
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
from django.http import JsonResponse



# @login_required(login_url='login')
def home(request):
    products = Product.objects.all()[:3] 
    return render(request, 'index.html', {'products': products})

@login_required(login_url='login')
def product_list(request):
    products = Product.objects.prefetch_related('images').all()  
    return render(request, 'product.html', {'products': products})

# @login_required(login_url='login')
def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        # Save the message to the database
        ContactMessage.objects.create(name=name, email=email, message=message)

        # Prepare the email content
        subject = f'New Contact Us Message from {name}'
        email_message = f"Sender's Email: {email}\n\nMessage: {message}"
        from_email = 'shreejienterprises84018@gmail.com'  # Your Gmail address
        recipient_list = ['shreejienterprises84018@gmail.com']  # Where you want to receive the email

        try:
            email_object = EmailMessage(
                subject=subject,
                body=email_message,
                from_email=from_email,
                to=recipient_list,
                reply_to=[email],  # Allows you to reply directly to the user
            )
            email_object.send(fail_silently=False)
            return JsonResponse({'success': True})
        except Exception as e:
            print("Email sending error:", str(e))  # Debugging Line - Print the error to console
            return JsonResponse({'success': False, 'error': str(e)})

    return render(request, 'store/contact.html')

def error_page(request):
    return render(request, 'store/error_page.html')

# @login_required(login_url='login')
def about(request):
    return render(request, 'about.html')

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)  # Use CustomUserCreationForm instead of UserCreationForm
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully. Please log in.')
            return redirect('login')
        else:
            messages.error(request, 'Registration failed. Please check the details and try again.')
    else:
        form = CustomUserCreationForm()  # Use your custom form here
    
    return render(request, 'auth/register.html', {'form': form})

User = get_user_model()

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)  # Make sure `username=email`

        if user is not None:
            if not user.is_active:
                messages.warning(request, "⚠️ Your account is inactive. Contact admin for help.")
                return redirect("login")  # Redirect back to login page

            login(request, user)
            

            # Redirect based on user type (admin or regular user)
            if user.is_superuser:
                messages.success(request, "✅ Login successful! Welcome back.")
                return redirect("/admin/")  # Redirect to Django admin panel
            else:
                messages.success(request, "✅ Login successful! Welcome back.")
                return redirect("home")  # Redirect to the home page
        else:
            messages.error(request, "❌ Invalid email or password.")
            return redirect("login")  # Redirect to login page

    return render(request, "auth/login.html")



@login_required(login_url="login")  # ✅ Protect user-only views
def product_list(request):
    products = Product.objects.prefetch_related("images").all()
    return render(request, "product.html", {"products": products})


def logout_view(request):
    logout(request)
    # messages.success(request, "✅ Logged out successfully!")
    return redirect('login') 

# forgot password 
otp_storage = {}  # Temporary storage for OTPs

def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)
            otp = random.randint(100000, 999999)
            otp_storage[email] = otp  # Store OTP temporarily

            # Send OTP via email
            send_mail(
                'Password Reset OTP',
                f'Your OTP for password reset is {otp}',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )

            messages.success(request, "✅ OTP has been sent to your email.")
            request.session['email'] = email  # Store email in session
            return redirect('verify_otp')

        except User.DoesNotExist:
            messages.error(request, "❌ Email not registered.")
    return render(request, 'auth/forgot_password.html')


def verify_otp(request):
    if request.method == "POST":
        email = request.session.get('email')
        otp = int(request.POST.get("otp"))

        if otp_storage.get(email) == otp:
            messages.success(request, "✅ OTP verified. You can reset your password now.")
            return redirect('reset_password')
        else:
            messages.error(request, "❌ Invalid OTP.")
    return render(request, 'auth/verify_otp.html')


def reset_password(request):
    if request.method == "POST":
        email = request.session.get('email')
        new_password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if new_password == confirm_password:
            try:
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                del otp_storage[email]  # Remove OTP from storage
                del request.session['email']  # Clear session data
                messages.success(request, "✅ Password reset successful. Please log in.")
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, "❌ An error occurred. Please try again.")
        else:
            messages.error(request, "❌ Passwords do not match.")
    return render(request, 'auth/reset_password.html')
