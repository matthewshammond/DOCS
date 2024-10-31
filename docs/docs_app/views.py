from django.shortcuts import render, redirect, get_object_or_404
from .models import Hospital, ProgramInfo, Invitation, UserProfile
from .forms import HospitalForm, CSVImportForm, RegisterForm, UserProfileForm, UserUpdateForm
import csv
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
import os
from django.conf import settings as django_settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from django.contrib.auth.models import User
from django.core import serializers
import json
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import datetime
import zipfile
import io
import json
import shutil
import tempfile


# Add hospital view
@login_required
def add_hospital(request):
    selected_program_id = request.session.get("selected_program_id")
    if not selected_program_id:
        messages.error(request, "Please select a program before adding hospitals.")
        return redirect("view_hospitals")

    if request.method == "POST":
        form = HospitalForm(request.POST)
        if form.is_valid():
            hospital = form.save(commit=False)
            hospital.program_id = selected_program_id
            hospital.save()
            return redirect("view_hospitals")
    else:
        form = HospitalForm()
    return render(request, "docs_app/add_hospital.html", {"form": form})


# Edit hospital view
@login_required
def edit_hospital(request, hospital_id):
    selected_program_id = request.session.get("selected_program_id")
    if not selected_program_id:
        messages.error(request, "No program selected.")
        return redirect("view_hospitals")

    hospital = get_object_or_404(
        Hospital, pk=hospital_id, program_id=selected_program_id
    )
    if request.method == "POST":
        form = HospitalForm(request.POST, instance=hospital)
        if form.is_valid():
            form.save()
            return redirect("view_hospitals")
    else:
        # Splitting latitude and longitude into degrees, minutes, and direction
        lat_deg, lat_min, lat_ns = hospital.latitude.split(" ")[
            :3
        ]  # Split 'xx xx.xx N/S'
        long_deg, long_min, long_ew = hospital.longitude.split(" ")[
            :3
        ]  # Split 'xxx xx.xx E/W'

        # Prepopulate the form with the split latitude and longitude
        form = HospitalForm(
            instance=hospital,
            initial={
                "lat_deg": lat_deg,
                "lat_min": lat_min,
                "lat_ns": lat_ns,
                "long_deg": long_deg,
                "long_min": long_min,
                "long_ew": long_ew,
            },
        )
    return render(
        request, "docs_app/edit_hospital.html", {"form": form, "hospital": hospital}
    )


# Delete hospital view
@login_required
def delete_hospital(request, hospital_id):
    hospital = get_object_or_404(Hospital, pk=hospital_id)
    hospital.delete()
    return redirect("view_hospitals")


# Export as CAD CSV
@login_required
def export_cad_csv(request):
    selected_program_id = request.session.get("selected_program_id")
    if not selected_program_id:
        messages.error(request, "No program selected.")
        return redirect("view_hospitals")

    # Get the program to use its code in the filename
    program = get_object_or_404(ProgramInfo, id=selected_program_id)
    
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{program.program_code}.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "LATITUDE",
            "LONGITUDE",
            "TITLE",
            "CAD Identifiers and/or Description",
            "FAA IDENTIFIER",
            "AIRPORT",
        ]
    )

    hospitals = Hospital.objects.filter(program_id=selected_program_id).order_by(
        "hospital_id"
    )
    for hospital in hospitals:
        writer.writerow(
            [
                hospital.latitude,
                hospital.longitude,
                hospital.hospital_id.upper(),
                f"{hospital.hospital_name}-{hospital.city}, {hospital.state}",
                (hospital.faa_identifier.upper() if hospital.faa_identifier else ""),
                hospital.airport,
            ]
        )
    return response


# Export as ForeFlight KML
@login_required
def export_foreflight_kml(request):
    selected_program_id = request.session.get("selected_program_id")
    if not selected_program_id:
        messages.error(request, "No program selected.")
        return redirect("view_hospitals")

    # Get the program to use its code in the filename
    program = get_object_or_404(ProgramInfo, id=selected_program_id)
    
    response = HttpResponse(content_type="application/vnd.google-earth.kml+xml")
    response["Content-Disposition"] = f'attachment; filename="{program.program_code}.kml"'

    def to_decimal_degrees(deg, min, direction):
        dd = float(deg) + (float(min) / 60)
        if direction in ["S", "W"]:
            dd = -dd
        return dd

    response.write('<?xml version="1.0" encoding="utf-8"?>\n')
    response.write('<kml xmlns="http://earth.google.com/kml/2.2">\n')
    response.write("<Document>\n")
    response.write(f"<name>{program.program_code.upper()}</name>\n")
    response.write(f"<description>{program.program_name}</description>\n")
    response.write('<Style id="style1">\n')
    response.write("    <IconStyle>\n")
    response.write("        <Icon>\n")
    response.write(
        "            <href>http://maps.google.com/mapfiles/kml/shapes/shaded_dot.png</href>\n"
    )
    response.write("        </Icon>\n")
    response.write("    </IconStyle>\n")
    response.write("</Style>\n")

    hospitals = Hospital.objects.filter(program_id=selected_program_id).order_by(
        "hospital_id"
    )
    for hospital in hospitals:
        lat_parts = hospital.latitude.split()
        long_parts = hospital.longitude.split()
        lat_dd = to_decimal_degrees(lat_parts[0], lat_parts[1], lat_parts[2])
        long_dd = to_decimal_degrees(long_parts[0], long_parts[1], long_parts[2])
        hospital_name_kml = hospital.hospital_name.replace(" ", "_")

        response.write("<Placemark>\n")
        response.write(f"    <name>{hospital_name_kml.upper()}</name>\n")
        response.write(
            f"    <description>{hospital.city.upper()}, {hospital.state.upper()} {hospital.hospital_id.upper()} {hospital.faa_identifier.upper() if hospital.faa_identifier else ''}\n\n{hospital.description}</description>\n"
        )
        response.write("    <styleUrl>#style1</styleUrl>\n")
        response.write("    <Point>\n")
        response.write(f"        <coordinates>{long_dd},{lat_dd},0</coordinates>\n")
        response.write("    </Point>\n")
        response.write("</Placemark>\n")

    response.write("</Document>\n")
    response.write("</kml>")
    return response


# Import CAD
@login_required
def import_csv(request):
    if request.method == "POST":
        form = CSVImportForm(request.POST, request.FILES)
        program_id = request.POST.get("program_id")

        if not program_id:
            return JsonResponse({"message": "No program selected."}, status=400)

        try:
            program = ProgramInfo.objects.get(id=program_id)
        except ProgramInfo.DoesNotExist:
            return JsonResponse(
                {"message": "Selected program does not exist."}, status=400
            )

        if form.is_valid():
            csv_file = request.FILES["csv_file"].read().decode("utf-8-sig").splitlines()
            reader = csv.DictReader(csv_file)

            for row in reader:
                try:
                    # Extract data from CSV
                    # Splitting latitude and longitude into degrees, minutes, and direction
                    latitude = row["LATITUDE"].strip()
                    lat_deg, lat_min, lat_ns = latitude.split(" ")[:3]
                    lat_wholemin, lat_decmin = lat_min.split(".")
                    if len(lat_deg) == 1:
                        lat_deg = "0" + lat_deg
                    if len(lat_wholemin) == 1:
                        lat_wholemin = "0" + lat_wholemin
                    if len(lat_decmin) == 1:
                        lat_decmin = "0" + lat_decmin
                    latitude = f"{lat_deg} {lat_wholemin}.{lat_decmin} {lat_ns}"
                    longitude = row["LONGITUDE"].strip()
                    long_deg, long_min, long_ns = longitude.split(" ")[:3]
                    long_wholemin, long_decmin = long_min.split(".")
                    if len(long_deg) == 2:
                        long_deg = "0" + long_deg
                    if len(long_wholemin) == 1:
                        long_wholemin = "0" + long_wholemin
                    if len(long_decmin) == 1:
                        long_decmin = "0" + long_decmin
                    longitude = f"{long_deg} {long_wholemin}.{long_decmin} {long_ns}"
                    hospital_id = row["TITLE"].strip()

                    # Handle the description field with optional city/state
                    description = row["CAD Identifiers and/or Description"].strip()
                    if "-" in description:
                        hospital_name, city_state = description.split("-", 1)
                        hospital_name = hospital_name.strip()
                        # Try to extract city and state if they exist
                        if "," in city_state:
                            city, state = city_state.split(",", 1)
                            city = city.strip()
                            state = state.strip()
                        else:
                            city = ""
                            state = ""
                    else:
                        hospital_name = description
                        city = ""
                        state = ""

                    faa_identifier = row["FAA IDENTIFIER"].strip()
                    airport = (
                        row["AIRPORT"].strip().lower() == "yes"
                        or row["AIRPORT"].strip().lower() == "true"
                    )  # Boolean conversion

                    # Ensure data is valid before saving
                    hospital = Hospital(
                        hospital_id=hospital_id[:5].upper(),
                        hospital_name=hospital_name,
                        city=city,
                        state=state,
                        faa_identifier=faa_identifier.upper() if faa_identifier else "",
                        airport=airport,
                        latitude=latitude,
                        longitude=longitude,
                        program=program,  # Use the selected program
                    )
                    hospital.save()
                except Exception as e:
                    return JsonResponse(
                        {"message": f"Error in row: {row}. Error: {e}"}, status=400
                    )

            return JsonResponse(
                {
                    "success": True,
                    "message": "CSV file imported successfully.",
                    "redirect": "/",
                }
            )

    return JsonResponse({"message": "Invalid request."}, status=400)


@login_required
def delete_all_hospitals(request):
    selected_program_id = request.session.get("selected_program_id")
    if not selected_program_id:
        messages.error(request, "No program selected.")
        return redirect("settings")

    if request.method == "POST":
        # Delete all hospital entries for the selected program
        Hospital.objects.filter(program_id=selected_program_id).delete()

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        else:
            messages.success(
                request, "All hospitals in the selected program have been deleted."
            )
            return redirect("settings")

    return render(request, "docs_app/delete_all.html")


# Add this new view to handle program settings
@login_required
def settings(request):
    # Check if user is admin (either staff or in Admin group)
    if not (request.user.is_staff or request.user.groups.filter(name='Admin').exists()):
        messages.error(request, "Access denied. You must be an administrator to view settings.")
        return redirect('view_hospitals')

    programs = ProgramInfo.objects.all().order_by("program_name")
    messages_dict = {"program_message": "", "delete_message": ""}

    if request.method == "POST":
        if "create_program" in request.POST:
            program_name = request.POST.get("program_name")
            program_code = request.POST.get("program_code")
            if program_name and program_code:
                ProgramInfo.objects.create(
                    program_name=program_name, program_code=program_code
                )
                messages_dict["program_message"] = "Program created successfully."

        elif "delete_program" in request.POST:
            program_id = request.POST.get("program_id")
            if program_id:
                try:
                    program = ProgramInfo.objects.get(id=program_id)
                    program.delete()
                    messages_dict["program_message"] = "Program deleted successfully."
                except ProgramInfo.DoesNotExist:
                    messages_dict["program_message"] = "Program not found."

        elif "edit_program" in request.POST:
            program_id = request.POST.get("program_id")
            program_name = request.POST.get("program_name")
            program_code = request.POST.get("program_code")
            if program_id and (program_name or program_code):
                try:
                    program = ProgramInfo.objects.get(id=program_id)
                    if program_name:
                        program.program_name = program_name
                    if program_code:
                        program.program_code = program_code
                    program.save()
                    messages_dict["program_message"] = "Program updated successfully."
                except ProgramInfo.DoesNotExist:
                    messages_dict["program_message"] = "Program not found."

    return render(
        request,
        "docs_app/settings.html",
        {
            "programs": programs,
            "program_message": messages_dict["program_message"],
            "delete_message": messages_dict["delete_message"],
        },
    )


@login_required
def view_hospitals(request):
    # Get programs based on user's groups
    if (request.user.is_staff or 
        request.user.groups.filter(name__in=["Admin", "Float_Pilots"]).exists()):
        programs = ProgramInfo.objects.all().order_by("program_name")
        user_programs = programs  # Staff, Admin, and Float Pilots can see all programs
    else:
        # Update to use program code directly instead of "Program_" prefix
        user_program_groups = request.user.groups.exclude(name__in=["Admin", "Float_Pilots"])
        program_codes = [g.name for g in user_program_groups]
        programs = ProgramInfo.objects.filter(program_code__in=program_codes).order_by("program_name")
        user_programs = programs  # Regular users can only see their assigned programs

    selected_program_id = request.session.get("selected_program_id")

    # If user only has access to one program, automatically select it
    if programs.count() == 1:
        selected_program_id = programs.first().id
        request.session["selected_program_id"] = selected_program_id

    # Get states for ForeFlight modal
    counties_dir = os.path.join(django_settings.STATIC_ROOT, "docs_app", "counties")
    states = []
    if os.path.exists(counties_dir):
        for file in os.listdir(counties_dir):
            if file.endswith("Counties.kml"):
                state_name = file[:-12].strip()  # Remove " Counties.kml"
                states.append(state_name)
    states.sort()

    # If the selected program no longer exists, clear it from session
    if selected_program_id and not programs.filter(id=selected_program_id).exists():
        selected_program_id = None
        request.session["selected_program_id"] = None

    # If no program is selected but programs exist, select the first one
    if not selected_program_id and programs.exists():
        selected_program_id = programs.first().id
        request.session["selected_program_id"] = selected_program_id

    # Get program and hospitals if a program is selected
    if selected_program_id:
        try:
            program = ProgramInfo.objects.get(id=selected_program_id)
            hospitals = Hospital.objects.filter(
                program_id=selected_program_id
            ).order_by("hospital_id")
        except ProgramInfo.DoesNotExist:
            program = None
            hospitals = Hospital.objects.none()
    else:
        program = None
        hospitals = Hospital.objects.none()

    # Handle program switching
    if request.method == "POST" and "switch_program" in request.POST:
        new_program_id = request.POST.get("program_id")
        if new_program_id:
            request.session["selected_program_id"] = int(new_program_id)
            return redirect("view_hospitals")

    context = {
        "hospitals": hospitals,
        "programs": programs,
        "selected_program": program,
        "states": states,  # Add states to context
        "show_program_selector": programs.count() > 1,  # Add this to control dropdown visibility
        "user_programs": user_programs,  # Add this to the context
    }
    return render(request, "docs_app/view_hospitals.html", context)


def custom_logout(request):
    logout(request)
    return redirect("login")


def custom_login(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("/")  # Redirect to the desired page after login
    else:
        form = AuthenticationForm()

    return render(request, "registration/login.html", {"form": form})


def register(request, token):
    try:
        invitation = Invitation.objects.get(token=token, accepted=False)
    except Invitation.DoesNotExist:
        return redirect("registration/invalid_invite.html")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Add user to assigned groups
            for group in invitation.groups.all():
                user.groups.add(group)

            invitation.accepted = True
            invitation.save()

            login(request, user)
            return redirect("/")
    else:
        form = RegisterForm(initial={"email": invitation.email})
    return render(request, "registration/register.html", {"form": form, "invitation": invitation})


def invalid_invite(request):
    return render(request, "registration/invalid_invite.html")


@login_required
def create_program_ajax(request):
    if (
        request.method == "POST"
        and request.headers.get("X-Requested-With") == "XMLHttpRequest"
    ):
        program_name = request.POST.get("program_name")
        program_code = request.POST.get("program_code")

        if program_name and program_code:
            try:
                program = ProgramInfo.objects.create(
                    program_name=program_name, program_code=program_code
                )
                return JsonResponse(
                    {
                        "success": True,
                        "program_id": program.id,
                        "message": "Program created successfully",
                    }
                )
            except Exception as e:
                return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse({"success": False, "message": "Invalid request"})


@login_required
def get_available_counties(request):
    """Get list of available county KML files."""
    # Try different possible paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    possible_paths = [
        os.path.join(base_dir, "docs_app", "static", "docs_app", "counties"),
        os.path.join(base_dir, "static", "docs_app", "counties"),
        "/vol/web/static/docs_app/counties"  # Docker volume path
    ]
    
    counties = []
    counties_dir = None

    # Try each path until we find one that exists
    for path in possible_paths:
        print(f"Trying path: {path}")  # Debug print
        if os.path.exists(path):
            print(f"Found valid path: {path}")  # Debug print
            counties_dir = path
            break

    if not counties_dir:
        print("No valid counties directory found!")  # Debug print
        return JsonResponse(
            {"counties": [], "error": "Counties directory not found"}
        )

    try:
        files = os.listdir(counties_dir)
        print(f"Files found: {files}")  # Debug print
        
        for file in files:
            if file.endswith("Counties.kml"):
                # Remove "Counties.kml" and trim any whitespace
                state_name = file[:-12].strip()
                counties.append(state_name)

        counties.sort()
        print(f"Counties found: {counties}")  # Debug print
        return JsonResponse({"counties": counties})

    except Exception as e:
        print(f"Error accessing counties directory: {str(e)}")  # Debug print
        return JsonResponse(
            {"counties": [], "error": f"Error accessing counties: {str(e)}"}
        )


@login_required
def export_county(request, state_name):
    """Export the selected county KML file."""
    if request.method == "GET":
        # Remove any trailing spaces from state_name
        state_name = state_name.strip()
        
        # Try different possible paths
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        possible_paths = [
            os.path.join(base_dir, "docs_app", "static", "docs_app", "counties"),
            os.path.join(base_dir, "static", "docs_app", "counties"),
            "/vol/web/static/docs_app/counties"  # Docker volume path
        ]
        
        file_path = None
        for path in possible_paths:
            temp_path = os.path.join(path, f"{state_name} Counties.kml")
            print(f"Trying path: {temp_path}")  # Debug print
            if os.path.exists(temp_path):
                print(f"Found valid file at: {temp_path}")  # Debug print
                file_path = temp_path
                break

        if file_path and os.path.exists(file_path):
            with open(file_path, "rb") as file:
                response = HttpResponse(
                    file.read(), content_type="application/vnd.google-earth.kml+xml"
                )
                response["Content-Disposition"] = (
                    f'attachment; filename="{state_name} Counties.kml"'
                )
                return response
                
        print(f"File not found for state: {state_name}")  # Debug print
        return HttpResponse("File not found", status=404)


class ProfileView(LoginRequiredMixin, UpdateView):
    template_name = 'docs_app/profile.html'
    success_url = '/'
    
    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def get_form_class(self):
        return UserProfileForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['user_form'] = UserUpdateForm(self.request.POST, instance=self.request.user)
        else:
            context['user_form'] = UserUpdateForm(instance=self.request.user)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        user_form = context['user_form']
        
        if user_form.is_valid():
            user_form.save()
            
        return super().form_valid(form)

@login_required
def account_view(request):
    # Ensure user has a profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your account has been updated!')
            return redirect('account')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    return render(request, 'docs_app/account.html', context)

@staff_member_required
def export_full_db(request):
    """Export full database including users and programs"""
    def serialize_datetime(obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return str(obj)

    data = {
        'users': list(User.objects.values(
            'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser'
        )),
        'programs': [
            {
                'id': p.id,
                'program_name': p.program_name,
                'program_code': p.program_code,
                'created_at': p.created_at.isoformat()
            }
            for p in ProgramInfo.objects.all()
        ],
        'hospitals': [
            {
                'hospital_id': h.hospital_id,
                'hospital_name': h.hospital_name,
                'city': h.city,
                'state': h.state,
                'latitude': h.latitude,
                'longitude': h.longitude,
                'faa_identifier': h.faa_identifier,
                'description': h.description,
                'airport': h.airport,
                'program_id': h.program_id
            }
            for h in Hospital.objects.all()
        ],
        'profiles': [
            {
                'id': p.id,
                'user_id': p.user_id,
                'profile_picture': str(p.profile_picture) if p.profile_picture else None
            }
            for p in UserProfile.objects.all()
        ]
    }
    
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'full_backup_{timestamp}.json'
    
    response = HttpResponse(
        json.dumps(data, indent=2, default=serialize_datetime),
        content_type='application/json'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@staff_member_required
def export_programs_db(request):
    """Export only programs and hospitals"""
    def serialize_datetime(obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return str(obj)

    data = {
        'programs': [
            {
                'id': p.id,
                'program_name': p.program_name,
                'program_code': p.program_code,
                'created_at': p.created_at.isoformat()
            }
            for p in ProgramInfo.objects.all()
        ],
        'hospitals': [
            {
                'hospital_id': h.hospital_id,
                'hospital_name': h.hospital_name,
                'city': h.city,
                'state': h.state,
                'latitude': h.latitude,
                'longitude': h.longitude,
                'faa_identifier': h.faa_identifier,
                'description': h.description,
                'airport': h.airport,
                'program_id': h.program_id
            }
            for h in Hospital.objects.all()
        ]
    }
    
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'programs_backup_{timestamp}.json'
    
    response = HttpResponse(
        json.dumps(data, indent=2, default=serialize_datetime),
        content_type='application/json'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@staff_member_required
def import_db(request):
    """Import database from backup file"""
    if request.method == 'POST' and request.FILES.get('db_file'):
        try:
            backup_file = request.FILES['db_file']
            data = json.loads(backup_file.read())
            
            # Check if it's a full backup or programs-only backup
            if 'users' in data:
                # Full backup
                User.objects.all().delete()  # Clear existing users
                for user_data in data['users']:
                    User.objects.create(**user_data)
                
                UserProfile.objects.all().delete()  # Clear existing profiles
                for profile_data in data['profiles']:
                    UserProfile.objects.create(**profile_data)
            
            # Import programs and hospitals
            ProgramInfo.objects.all().delete()  # Clear existing programs
            Hospital.objects.all().delete()  # Clear existing hospitals
            
            for program_data in data['programs']:
                ProgramInfo.objects.create(**program_data)
            
            for hospital_data in data['hospitals']:
                Hospital.objects.create(**hospital_data)
            
            messages.success(request, 'Database imported successfully!')
        except Exception as e:
            messages.error(request, f'Error importing database: {str(e)}')
        
        return redirect('settings')
    
    messages.error(request, 'No file provided')
    return redirect('settings')

@login_required
def export_program_kml(request, program_code):
    """Export a single program's KML file"""
    try:
        program = ProgramInfo.objects.get(program_code=program_code)
        response = HttpResponse(content_type="application/vnd.google-earth.kml+xml")
        response["Content-Disposition"] = f'attachment; filename="{program_code}.kml"'

        def to_decimal_degrees(deg, min, direction):
            dd = float(deg) + (float(min) / 60)
            if direction in ["S", "W"]:
                dd = -dd
            return dd

        response.write('<?xml version="1.0" encoding="utf-8"?>\n')
        response.write('<kml xmlns="http://earth.google.com/kml/2.2">\n')
        response.write("<Document>\n")
        response.write(f"<name>{program_code.upper()}</name>\n")
        response.write(f"<description>{program.program_name}</description>\n")
        response.write('<Style id="style1">\n')
        response.write("    <IconStyle>\n")
        response.write("        <Icon>\n")
        response.write(
            "            <href>http://maps.google.com/mapfiles/kml/shapes/shaded_dot.png</href>\n"
        )
        response.write("        </Icon>\n")
        response.write("    </IconStyle>\n")
        response.write("</Style>\n")

        hospitals = Hospital.objects.filter(program=program).order_by("hospital_id")
        for hospital in hospitals:
            lat_parts = hospital.latitude.split()
            long_parts = hospital.longitude.split()
            lat_dd = to_decimal_degrees(lat_parts[0], lat_parts[1], lat_parts[2])
            long_dd = to_decimal_degrees(long_parts[0], long_parts[1], long_parts[2])
            hospital_name_kml = hospital.hospital_name.replace(" ", "_")

            response.write("<Placemark>\n")
            response.write(f"    <name>{hospital_name_kml.upper()}</name>\n")
            response.write(
                f"    <description>{hospital.city.upper()}, {hospital.state.upper()} {hospital.hospital_id.upper()} {hospital.faa_identifier.upper() if hospital.faa_identifier else ''}\n\n{hospital.description}</description>\n"
            )
            response.write("    <styleUrl>#style1</styleUrl>\n")
            response.write("    <Point>\n")
            response.write(f"        <coordinates>{long_dd},{lat_dd},0</coordinates>\n")
            response.write("    </Point>\n")
            response.write("</Placemark>\n")

        response.write("</Document>\n")
        response.write("</kml>")
        return response
    except ProgramInfo.DoesNotExist:
        return HttpResponse("Program not found", status=404)

@login_required
def export_county_names(request, state_name):
    """Export the county names KML file for a state"""
    file_path = os.path.join(django_settings.STATIC_ROOT, "docs_app", "names", f"{state_name} County Names.kml")
    if os.path.exists(file_path):
        with open(file_path, "rb") as file:
            response = HttpResponse(file.read(), content_type="application/vnd.google-earth.kml+xml")
            response["Content-Disposition"] = f'attachment; filename="{state_name} County Names.kml"'
            return response
    return HttpResponse("File not found", status=404)

def get_user_programs(request):
    """Get programs accessible to the user"""
    if (request.user.is_staff or 
        request.user.groups.filter(name__in=["Admin", "Float_Pilots"]).exists()):
        return ProgramInfo.objects.all()
    
    user_program_groups = request.user.groups.exclude(name__in=["Admin", "Float_Pilots"])
    program_codes = [g.name for g in user_program_groups]
    return ProgramInfo.objects.filter(program_code__in=program_codes)

@login_required
def export_foreflight(request):
    # Add this at the beginning of the view
    user_programs = get_user_programs(request)
    if request.method == 'POST':
        programs = json.loads(request.POST.get('programs', '[]'))
        
        # Validate that user has access to selected programs
        for program in programs:
            if not user_programs.filter(program_code=program['code']).exists():
                return JsonResponse({'error': 'Access denied to one or more programs'}, status=403)
        
        states = json.loads(request.POST.get('states', '[]'))
        download_option = request.POST.get('download_option')

        if not programs and not states:
            return JsonResponse({'error': 'Please select at least one program or state'}, status=400)

        if download_option == 'individual':
            # Handle individual downloads
            files = []
            
            # Add program KML files if any programs are selected
            for program in programs:
                files.append({
                    'name': f"{program['code']}.kml",
                    'url': f"/export/program-kml/{program['code']}/"
                })

            # Add county files if any states are selected
            for state in states:
                files.append({
                    'name': f"{state} Counties.kml",
                    'url': f"/export/county/{state}/"
                })
                files.append({
                    'name': f"{state} County Names.kml",
                    'url': f"/export/county-names/{state}/"
                })

            return JsonResponse({'files': files})

        else:
            # Content pack requires at least one program
            if not programs:
                return JsonResponse({'error': 'Please select at least one program for content pack'}, status=400)

            program = programs[0]  # Use first program for content pack name
            
            # Create zip file in memory
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Create the directory structure
                base_dir = program['code']
                zip_file.writestr(f"{base_dir}/byop/.keep", "")  # Empty file to maintain directory
                
                # Add manifest.json with correct format
                manifest_data = {
                    "name": program['code'],
                    "abbreviation": "DOCS.V1",
                    "version": 1.0,
                    "organizationName": program['name']
                }
                zip_file.writestr(f"{base_dir}/manifest.json", json.dumps(manifest_data, indent=2))
                
                # Add program KML files to navdata
                for prog in programs:
                    program_kml = generate_program_kml(prog['code'])
                    zip_file.writestr(f"{base_dir}/navdata/{prog['code']}.kml", program_kml)

                # Add county files
                for state in states:
                    # Add Counties.kml to layers
                    counties_path = os.path.join(django_settings.STATIC_ROOT, "docs_app", "counties", f"{state} Counties.kml")
                    if os.path.exists(counties_path):
                        with open(counties_path, 'rb') as f:
                            zip_file.writestr(f"{base_dir}/layers/{state} Counties.kml", f.read())
                    
                    # Add County Names.kml to navdata
                    names_path = os.path.join(django_settings.STATIC_ROOT, "docs_app", "names", f"{state} County Names.kml")
                    if os.path.exists(names_path):
                        with open(names_path, 'rb') as f:
                            zip_file.writestr(f"{base_dir}/navdata/{state} County Names.kml", f.read())

            # Prepare the response
            zip_buffer.seek(0)
            response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{program["code"]}.zip"'
            return response

    return JsonResponse({'error': 'Invalid request'}, status=400)

def generate_program_kml(program_code):
    """Generate KML content for a program"""
    try:
        program = ProgramInfo.objects.get(program_code=program_code)
        
        def to_decimal_degrees(deg, min, direction):
            dd = float(deg) + (float(min) / 60)
            if direction in ["S", "W"]:
                dd = -dd
            return dd

        kml_content = '<?xml version="1.0" encoding="utf-8"?>\n'
        kml_content += '<kml xmlns="http://earth.google.com/kml/2.2">\n'
        kml_content += "<Document>\n"
        kml_content += f"<name>{program_code.upper()}</name>\n"
        kml_content += f"<description>{program.program_name}</description>\n"
        kml_content += '<Style id="style1">\n'
        kml_content += "    <IconStyle>\n"
        kml_content += "        <Icon>\n"
        kml_content += "            <href>http://maps.google.com/mapfiles/kml/shapes/shaded_dot.png</href>\n"
        kml_content += "        </Icon>\n"
        kml_content += "    </IconStyle>\n"
        kml_content += "</Style>\n"

        hospitals = Hospital.objects.filter(program=program).order_by("hospital_id")
        for hospital in hospitals:
            lat_parts = hospital.latitude.split()
            long_parts = hospital.longitude.split()
            lat_dd = to_decimal_degrees(lat_parts[0], lat_parts[1], lat_parts[2])
            long_dd = to_decimal_degrees(long_parts[0], long_parts[1], long_parts[2])
            hospital_name_kml = hospital.hospital_name.replace(" ", "_")

            kml_content += "<Placemark>\n"
            kml_content += f"    <name>{hospital_name_kml.upper()}</name>\n"
            kml_content += f"    <description>{hospital.city.upper()}, {hospital.state.upper()} {hospital.hospital_id.upper()} {hospital.faa_identifier.upper() if hospital.faa_identifier else ''}\n\n{hospital.description}</description>\n"
            kml_content += "    <styleUrl>#style1</styleUrl>\n"
            kml_content += "    <Point>\n"
            kml_content += f"        <coordinates>{long_dd},{lat_dd},0</coordinates>\n"
            kml_content += "    </Point>\n"
            kml_content += "</Placemark>\n"

        kml_content += "</Document>\n"
        kml_content += "</kml>"
        return kml_content
    except ProgramInfo.DoesNotExist:
        return ""
