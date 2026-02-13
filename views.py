import json
import os
from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse, JsonResponse
from datetime import datetime


BERICHTE_DATEI = "/var/www/static/berichte.json" #Kristina Baotic
VIP_ANTRAEGE_DATEI = "/var/www/static/vip_antraege.json"
MODULE_DATEI = "/var/www/static/module.json" #Kristina Baotic
USERS_FILE = "/var/www/django-projekt/meine_app/users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as datei:
            return json.load(datei)
    return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as datei:
        json.dump(users, datei, indent=2, ensure_ascii=False)

def get_initials(firstname, lastname):
    
    if firstname:  
        first = firstname[0].upper()
    else:
        first = ""
    
    if lastname:  
        last = lastname[0].upper()
    else:
        last = ""
    
    return first + last

#Registrierung

def registrieren(request):
    if request.method == "POST":
        firstname = request.POST.get("firstname", "").strip()
        lastname = request.POST.get("lastname", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password-confirm", "")
        

        if password != password_confirm:
            return render(request, "meine_app/registrieren.html", {
                "error": "Passwörter stimmen nicht überein"
            })
        
        users = load_users()
        
        for username, user_data in users.items():
            if user_data.get("email", "").lower() == email:
                return render(request, "meine_app/registrieren.html", {
                    "error": "Diese E-Mail ist bereits registriert"
                })
        
        username = email.split("@")[0]
        
        original_username = username
        counter = 1
        while username in users:
            username = f"{original_username}{counter}"
            counter += 1
        
        users[username] = {
            "firstname": firstname,
            "lastname": lastname,
            "email": email,
            "password": password,
            "role": "user"
        }
        
        save_users(users)
        
        request.session["username"] = username
        request.session["user_role"] = "user"
        request.session["user_firstname"] = firstname
        request.session["user_lastname"] = lastname
        request.session["user_email"] = email
        
        return redirect("/dashboard") 
    
    return render(request, "meine_app/registrieren.html")

#Login

def login(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        
        users = load_users()
        
        found_user = None
        found_username = None
        
        for username, user_data in users.items():
            if user_data.get("email", "").lower() == email:
                found_user = user_data
                found_username = username
                break
        
        if found_user and found_user.get("password") == password:
            request.session["username"] = found_username
            request.session["user_role"] = found_user.get("role", "user")
            request.session["user_firstname"] = found_user.get("firstname", "")
            request.session["user_lastname"] = found_user.get("lastname", "")
            request.session["user_email"] = found_user.get("email", "")
            
            return redirect("/dashboard")  
        else:
            return render(request, "meine_app/login.html", {
                "error": "E-Mail oder Passwort falsch"
            })
        
    #Cookie - KRISTINA BAOTIC
    last_email = request.COOKIES.get("last_user_email", "")

    erster_besuch = not request.COOKIES.get("cookie_hinweis_gesehen", False)

    context = {
        "last_email": last_email,
        "erster_besuch": erster_besuch
    }

    return render(request, "meine_app/login.html")

#Logout

def logout_view(request):
    request.session.flush()
    return redirect("/login")


#Datenmanegement für VIP
def vip_datenmanagement(request):
    if "username" not in request.session:
        return redirect("login")

    if request.session.get("user_role") not in ["vip", "admin"]:
        return redirect("dashboard")
    
    username = request.session.get("username")
    users = load_users()
    user_data = users.get(username, {})
    
    context = {
        "user": {
            "username": username,
            "firstname": user_data.get("firstname", ""),
            "lastname": user_data.get("lastname", ""),
            "email": user_data.get("email", ""),
            "role": user_data.get("role", "user"),
            "initials": get_initials(
                user_data.get("firstname", ""),
                user_data.get("lastname", "")
            )
        }
    }
    
    return render(request, "meine_app/vip_datenmanagement.html", context)

def load_vip_antraege():
    if os.path.exists(VIP_ANTRAEGE_DATEI):
        with open(VIP_ANTRAEGE_DATEI, "r", encoding="utf-8") as datei:
            try:
                return json.load(datei)
            except:
                return []
    return []

def save_vip_antraege(antraege):
    with open(VIP_ANTRAEGE_DATEI, "w", encoding="utf-8") as datei:
        json.dump(antraege, datei, indent=2, ensure_ascii=False)

#Vip Antrag stellen
def vip_werden(request):
    if "username" not in request.session:
        return redirect("login")
    
    username = request.session["username"]
    users = load_users()
    user_data = users.get(username, {})

    if user_data.get("role") in ["vip", "admin"]:
        return redirect("dashboard")

    antraege = load_vip_antraege()
    offener_antrag = None
    for antrag in antraege:
        if antrag["username"] == username and antrag["status"] == "pending":
            offener_antrag = antrag
            break
    
    if request.method == "POST":
        begruendung = request.POST.get("begruendung", "").strip()
        
        if not begruendung:
            context = {
                "user": {
                    "role": user_data.get("role", "user"),
                    "initials": get_initials(
                        user_data.get("firstname", ""),
                        user_data.get("lastname", "")
                    )
                },
                "error": "Bitte geben Sie eine Begründung an"
            }
            return render(request, "meine_app/vip_werden.html", context)
        
        neuer_antrag = {
            "username": username,
            "firstname": user_data.get("firstname", ""),
            "lastname": user_data.get("lastname", ""),
            "email": user_data.get("email", ""),
            "begruendung": begruendung,
            "antrag_typ": "vip",
            "status": "pending", 
            "erstellt_am": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "bearbeitet_am": None,
            "bearbeitet_von": None
        }
        antraege.insert(0, neuer_antrag)
        save_vip_antraege(antraege)
        
        return redirect("dashboard")
    
    context = {
        "user": {
            "role": user_data.get("role", "user"),
            "initials": get_initials(
                user_data.get("firstname", ""),
                user_data.get("lastname", "")
            )
        },
        "offener_antrag": offener_antrag
    }
    
    return render(request, "meine_app/vip_werden.html", context)

#Admin Antrag
def admin_antraege(request):
    if "username" not in request.session:
        return redirect("login")
    
    if request.session.get("user_role") != "admin":
        return redirect("dashboard")
    
    antraege = load_vip_antraege()

    pending_vip = []
    pending_admin = []
    approved_vip = []
    approved_admin = []
    rejected_vip = []
    rejected_admin = []
    
    for antrag in antraege:
        status = antrag["status"]
        typ = antrag.get("antrag_typ", "vip") 
        
        if status == "pending":
            if typ == "vip":
                pending_vip.append(antrag)
            else:
                pending_admin.append(antrag)
        
        elif status == "approved":
            if typ == "vip":
                approved_vip.append(antrag)
            else:
                approved_admin.append(antrag)
        
        elif status == "rejected":
            if typ == "vip":
                rejected_vip.append(antrag)
            else:
                rejected_admin.append(antrag)

    context = {
        "user": {
            "role": request.session.get("user_role", "user"),
            "initials": get_initials(
                request.session.get("user_firstname", ""),
                request.session.get("user_lastname", "")
            )
        },
        "pending_vip": pending_vip,
        "pending_admin": pending_admin,
        "approved_vip": approved_vip,
        "approved_admin": approved_admin,
        "rejected_vip": rejected_vip,
        "rejected_admin": rejected_admin,
        "anzahl_pending_vip": len(pending_vip),
        "anzahl_pending_admin": len(pending_admin)
    }
    
    return render(request, "meine_app/admin_antraege.html", context)

#Antrag genehmigen
def antrag_genehmigen(request, username):
    if "username" not in request.session:
        return redirect("login")
    
    if request.session.get("user_role") != "admin":
        return redirect("dashboard")
    
    antraege = load_vip_antraege()
    users = load_users()
    
    for antrag in antraege:
        if antrag["username"] == username and antrag["status"] == "pending":
            antrag["status"] = "approved"
            antrag["bearbeitet_am"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            antrag["bearbeitet_von"] = request.session.get("username")
            
            if username in users:
                if antrag.get("antrag_typ") == "admin":
                    users[username]["role"] = "admin"
                else:
                    users[username]["role"] = "vip"
                save_users(users)
            
            break
    
    save_vip_antraege(antraege)
    return redirect("admin_antraege")

#Antrag ablehnen
def antrag_ablehnen(request, username):
    if "username" not in request.session:
        return redirect("/login")

    if request.session.get("user_role") != "admin":
        return redirect("/dashboard")
    
    antraege = load_vip_antraege()
    
    for antrag in antraege:
        if antrag["username"] == username and antrag["status"] == "pending":
            antrag["status"] = "rejected"
            antrag["bearbeitet_am"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            antrag["bearbeitet_von"] = request.session.get("username")
            break
    
    save_vip_antraege(antraege)
    return redirect("admin_antraege")

#Admin werden
def administrator_werden(request):
    if "username" not in request.session:
        return redirect("login")
    
    username = request.session["username"]
    users = load_users()
    user_data = users.get(username, {})
    
    if user_data.get("role") != "vip":
        return redirect("dashboard")
    
    antraege = load_vip_antraege()
    offener_antrag = None
    for antrag in antraege:
        if antrag["username"] == username and antrag["status"] == "pending" and antrag.get("antrag_typ") == "admin":
            offener_antrag = antrag
            break
    
    if request.method == "POST":
        begruendung = request.POST.get("begruendung", "").strip()
        
        if not begruendung:
            context = {
                "user": {
                    "role": user_data.get("role", "user"),
                    "initials": get_initials(
                        user_data.get("firstname", ""),
                        user_data.get("lastname", "")
                    )
                },
                "error": "Bitte geben Sie eine Begründung an"
            }
            return render(request, "meine_app/administrator_werden.html", context)
        
        neuer_antrag = {
            "username": username,
            "firstname": user_data.get("firstname", ""),
            "lastname": user_data.get("lastname", ""),
            "email": user_data.get("email", ""),
            "begruendung": begruendung,
            "antrag_typ": "admin", 
            "status": "pending",
            "erstellt_am": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "bearbeitet_am": None,
            "bearbeitet_von": None
        }
       
        antraege.insert(0, neuer_antrag)
        save_vip_antraege(antraege)
        
        return redirect("dashboard")
    
    context = {
        "user": {
            "role": user_data.get("role", "user"),
            "initials": get_initials(
                user_data.get("firstname", ""),
                user_data.get("lastname", "")
            )
        },
        "offener_antrag": offener_antrag
    }
    
    return render(request, "meine_app/administrator_werden.html", context)

#Benutzerverwaltung

def admin_benutzerverwaltung(request):
    if "username" not in request.session:
        return redirect("login")
    
    if request.session.get("user_role") != "admin":
        return redirect("dashboard")
    
    users = load_users()
    
    anzahl_gesamt = len(users)
    anzahl_admin = 0
    anzahl_vip = 0
    anzahl_user = 0
    
    user_liste = []
    
    for username, user_data in users.items():
        rolle = user_data.get("role", "user")
        if rolle == "admin":
            anzahl_admin += 1
        elif rolle == "vip":
            anzahl_vip += 1
        elif rolle == "user":
            anzahl_user += 1
        
        user_liste.append({
            "username": username,
            "firstname": user_data.get("firstname", ""),
            "lastname": user_data.get("lastname", ""),
            "email": user_data.get("email", ""),
            "role": rolle,
            "created_at": user_data.get("created_at", ""),
            "initials": get_initials(
                user_data.get("firstname", ""),
                user_data.get("lastname", "")
            )
        })
    
    context = {
        "user": {
            "role": request.session.get("user_role", "user"),
            "initials": get_initials(
                request.session.get("user_firstname", ""),
                request.session.get("user_lastname", "")
            )
        },
        "anzahl_gesamt": anzahl_gesamt,
        "anzahl_admin": anzahl_admin,
        "anzahl_vip": anzahl_vip,
        "anzahl_user": anzahl_user,
        "user_liste": user_liste
    }
    
    return render(request, "meine_app/admin_benutzerverwaltung.html", context)

#Benutzer löschen
def benutzer_loeschen(request, username):
    if "username" not in request.session:
        return redirect("login")
   
    if request.session.get("user_role") != "admin":
        return redirect("dashboard")

    if username == request.session.get("username"):
        return redirect("admin_benutzerverwaltung")
    
    users = load_users()
    
    if username in users:
        del users[username]
        save_users(users)
    
    return redirect("admin_benutzerverwaltung") 

#Export

def export_json(request):
    if "username" not in request.session:
        return redirect("login")
    
    if request.session.get("user_role") not in ["vip", "admin"]:
        return redirect("dashboard")
    
    username = request.session.get("username")
    
    if os.path.exists(BERICHTE_DATEI):
        with open(BERICHTE_DATEI, "r") as datei:
            try:
                alle_berichte = json.load(datei)
            except:
                alle_berichte = []
    else:
        alle_berichte = []
    
    eigene_berichte = []
    for bericht in alle_berichte:
        if bericht.get("benutzer") == username:
            eigene_berichte.append(bericht)

    json_string = json.dumps(eigene_berichte, indent=2, ensure_ascii=False)

    response = HttpResponse(json_string, content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="berichte_{username}.json"'
    return response


def export_csv(request):
    if "username" not in request.session:
        return redirect("login")
    
    if request.session.get("user_role") not in ["vip", "admin"]:
        return redirect("dashboard")
    
    username = request.session.get("username")

    if os.path.exists(BERICHTE_DATEI):
        with open(BERICHTE_DATEI, "r") as datei:
            try:
                alle_berichte = json.load(datei)
            except:
                alle_berichte = []
    else:
        alle_berichte = []
    
    eigene_berichte = []
    for bericht in alle_berichte:
        if bericht.get("benutzer") == username:
            eigene_berichte.append(bericht)
    
    csv_text = "Datum;Stunden;Minuten;Modul;Beschreibung;Benutzer\n"
    
    for bericht in eigene_berichte:
        zeile = f"{bericht.get('datum', '')};{bericht.get('stunden', '')};{bericht.get('minuten', '')};{bericht.get('modul', '')};{bericht.get('beschreibung', '')};{bericht.get('benutzer', '')}\n"
        csv_text += zeile
    
    response = HttpResponse(csv_text, content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="berichte_{username}.csv"'
    return response


def export_xml(request):
    if "username" not in request.session:
        return redirect("login")
    
    if request.session.get("user_role") not in ["vip", "admin"]:
        return redirect("dashboard")
    
    username = request.session.get("username")
    
    if os.path.exists(BERICHTE_DATEI):
        with open(BERICHTE_DATEI, "r") as datei:
            try:
                alle_berichte = json.load(datei)
            except:
                alle_berichte = []
    else:
        alle_berichte = []

    eigene_berichte = []
    for bericht in alle_berichte:
        if bericht.get("benutzer") == username:
            eigene_berichte.append(bericht)

    xml_text = '<berichte>\n'
    
    for bericht in eigene_berichte:
        xml_text += f'  <bericht '
        xml_text += f'datum="{bericht.get("datum", "")}" '
        xml_text += f'stunden="{bericht.get("stunden", "")}" '
        xml_text += f'minuten="{bericht.get("minuten", "")}" '
        xml_text += f'modul="{bericht.get("modul", "")}" '
        xml_text += f'beschreibung="{bericht.get("beschreibung", "")}" '
        xml_text += f'benutzer="{bericht.get("benutzer", "")}"'
        xml_text += ' />\n'
    
    xml_text += '</berichte>'
    
    response = HttpResponse(xml_text, content_type='application/xml; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="berichte_{username}.xml"'
    return response
