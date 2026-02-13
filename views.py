import json
import os
from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse, JsonResponse
from datetime import datetime


BERICHTE_DATEI = "/var/www/static/berichte.json"
VIP_ANTRAEGE_DATEI = "/var/www/static/vip_antraege.json"
MODULE_DATEI = "/var/www/static/module.json"
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

#Registrierung - Claire Dörr

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

#Login - Claire Dörr

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
        

    #Cookie - Kristina Baotic
    last_email = request.COOKIES.get("last_user_email", "")

    erster_besuch = not request.COOKIES.get("cookie_hinweis_gesehen", False)

    context = {
        "last_email": last_email,
        "erster_besuch": erster_besuch
    }

    return render(request, "meine_app/login.html")

#Logout - Claire Dörr

def logout_view(request):
    request.session.flush()
    return redirect("/login")

#Profil - Kristina Baotic
def profil(request):
    if "username" not in request.session:
        return redirect("/login")
    
    username = request.session["username"]
    users = load_users()
    user_data = users.get(username, {})
    
    success = False
    error = None
    
    if request.method == "POST":
        form_type = request.POST.get("form_type")
        
        if form_type == "personal_info":
            new_firstname = request.POST.get("firstname", "").strip()
            new_lastname = request.POST.get("lastname", "").strip()
            new_email = request.POST.get("email", "").strip().lower()
            
            if not new_firstname or not new_lastname or not new_email:
                error = "Alle Felder sind erforderlich"
            else:
                email_exists = False
                for other_username, other_data in users.items():
                    if other_username != username:
                        if other_data.get("email", "").lower() == new_email:
                            email_exists = True
                            break
                
                if email_exists:
                    error = "Diese E-Mail wird bereits verwendet"
                else:
                    user_data["firstname"] = new_firstname
                    user_data["lastname"] = new_lastname
                    user_data["email"] = new_email
                    users[username] = user_data
                    save_users(users)
                    
                    request.session["user_firstname"] = new_firstname
                    request.session["user_lastname"] = new_lastname
                    request.session["user_email"] = new_email
                    
                    success = True
        
        elif form_type == "change_password":
            current_password = request.POST.get("current-password", "")
            new_password = request.POST.get("new-password", "")
            password_confirm = request.POST.get("password-confirm", "")
            
            if user_data.get("password") != current_password:
                error = "Aktuelles Passwort ist falsch"
            elif new_password != password_confirm:
                error = "Passwörter stimmen nicht überein"
            else:
                user_data["password"] = new_password
                users[username] = user_data
                save_users(users)
                success = True
        
        elif form_type == "delete_account":
            del users[username]
            save_users(users)

            request.session.flush()
            
            return redirect("/login")

    context = {
        "user": {
            "username": username,
            "firstname": user_data.get("firstname", ""),
            "lastname": user_data.get("lastname", ""),
            "email": user_data.get("email", ""),
            "role": user_data.get("role", "user"),
            "created_at": user_data.get("created_at", ""),
            "initials": get_initials(
                user_data.get("firstname", ""),
                user_data.get("lastname", "")
            )
        },
        "success": success,
        "error": error
    }
    
    return render(request, "meine_app/profil.html", context)

#Datenmanegement für VIP - Claire Dörr
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

#Vip werden - Claire Dörr 
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

#Admin Antrag - Claire Dörr
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

#Antrag genehmigen - Claire Dörr
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

#Antrag ablehnen - Claire Dörr
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

#Admin werden _ Claire Dörr
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

#Benutzerverwaltung - Claire Dörr

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

#Benutzer löschen - Claire Dörr
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

#Export - Claire Dörr

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

#Dashboard - Krisitna Baotic

def dashboard(request):
    if "username" not in request.session:
        return redirect("/login")
    
    username = request.session.get("username")
    
    if os.path.exists(BERICHTE_DATEI):
        with open(BERICHTE_DATEI, "r", encoding='utf-8') as datei:
            try: 
                alle_berichte = json.load(datei)
                
                berichte = []
                for bericht in alle_berichte:
                    if bericht.get("benutzer") == username:
                        berichte.append(bericht)

                for bericht in berichte:
                    if bericht.get("datum"):
                        datum_teile = bericht["datum"].split("-")
                        if len(datum_teile) == 3:
                            bericht["datum_formatiert"] = f"{datum_teile[2]}.{datum_teile[1]}.{datum_teile[0]}"
                        else:
                            bericht["datum_formatiert"] = bericht["datum"]
                    else:
                        bericht["datum_formatiert"] = "Kein Datum"
            except:
                berichte = []
    else:
        berichte = []
    
    context = {
        "user": {
            "username": request.session.get("username"),
            "firstname": request.session.get("user_firstname"),
            "lastname": request.session.get("user_lastname"),
            "email": request.session.get("user_email"),
            "role": request.session.get("user_role", "user"),
            "initials": get_initials(
                request.session.get("user_firstname", ""),
                request.session.get("user_lastname", "")
            )
        },
        "berichte": berichte
    }
    
    return render(request, "meine_app/dashboard.html", context)
 

def neuer_bericht(request):
    if "username" not in request.session:
        return redirect("login")
    
    module = load_module()     
    context = {
        "user": {
            "role": request.session.get("user_role", "user"),
            "initials": get_initials(
                request.session.get("user_firstname", ""),
                request.session.get("user_lastname", "")
            )
        },
        "module": module
    }
    
    return render(request, "meine_app/neuer_bericht.html", context)

def bericht_speichern(request):
    if request.method == "POST":
        datum = request.POST.get("datum", "")
        stunden = request.POST.get("stunden", "")
        minuten = request.POST.get("minuten", "")
        modul = request.POST.get("modul", "")
        beschreibung = request.POST.get("beschreibung", "")
        
        if os.path.exists(BERICHTE_DATEI):
            with open(BERICHTE_DATEI, "r") as datei:
                try:
                    berichte = json.load(datei)
                except:
                    berichte = []
        else:
            berichte = []
        

        neuer_bericht = {
            "datum": datum,
            "stunden": stunden,
            "minuten": minuten,
            "modul": modul,
            "beschreibung": beschreibung,
            "benutzer": request.session.get("username", "unbekannt")
        }
        
        berichte.insert(0, neuer_bericht)
      
        with open(BERICHTE_DATEI, "w") as datei:
            json.dump(berichte, datei, indent=2)
        
        return redirect("dashboard")
    
    return HttpResponse("Fehler beim Speichern")

def zeituebersicht(request):
    if "username" not in request.session:
        return redirect("/login")
    
    username = request.session.get("username")
    
    if os.path.exists(BERICHTE_DATEI):
        with open(BERICHTE_DATEI, "r") as datei:
            try:
                alle_berichte = json.load(datei)
            except:
                alle_berichte = []
    else:
        alle_berichte = []
    
    eigene_berichte = [b for b in alle_berichte if b.get("benutzer") == username]
    
    modul_stats = {}
    gesamt_minuten = 0
    
    for bericht in eigene_berichte:
        modul = bericht.get("modul", "Unbekannt")
        stunden = int(bericht.get("stunden", 0))
        minuten = int(bericht.get("minuten", 0))
        
        total_minuten = (stunden * 60) + minuten
        gesamt_minuten += total_minuten
        
        if modul not in modul_stats:
            modul_stats[modul] = {
                "minuten": 0,
                "anzahl": 0
            }
        
        modul_stats[modul]["minuten"] += total_minuten
        modul_stats[modul]["anzahl"] += 1
    
    modul_liste = []
    for modul, stats in modul_stats.items():
        minuten = stats["minuten"]
        stunden = minuten // 60
        rest_minuten = minuten % 60
        
        prozent = (minuten / gesamt_minuten * 100) if gesamt_minuten > 0 else 0
        
        umgerechnet_std = minuten / 60
        umgerechnet_h = int(umgerechnet_std)
        umgerechnet_m = int((umgerechnet_std - umgerechnet_h) * 60)
        
        modul_liste.append({
            "name": modul,
            "minuten": minuten,
            "zeit_text": f"{minuten} Min",
            "umgerechnet": f"{umgerechnet_h}h {umgerechnet_m}min",
            "prozent": round(prozent, 2),
            "anteil": f"{prozent:.2f}%",
            "anzahl": stats["anzahl"]
        })

    modul_liste.sort(key=lambda x: x["minuten"], reverse=True)

    gesamt_stunden = gesamt_minuten // 60
    gesamt_rest_minuten = gesamt_minuten % 60
    
    from datetime import datetime
    
    context = {
        "user": {
            "username": username,
            "firstname": request.session.get("user_firstname", ""),
            "lastname": request.session.get("user_lastname", ""),
            "email": request.session.get("user_email", ""),
            "role": request.session.get("user_role", "user"),
            "initials": get_initials(
                request.session.get("user_firstname", ""),
                request.session.get("user_lastname", "")
            )
        },
        "gesamt_minuten": gesamt_minuten,
        "gesamt_stunden": gesamt_stunden,
        "gesamt_rest_minuten": gesamt_rest_minuten,
        "gesamt_text": f"{gesamt_stunden} Stunden {gesamt_rest_minuten} Minuten",
        "modul_liste": modul_liste,
        "anzahl_berichte": len(eigene_berichte),
        "datum_erstellt": datetime.now().strftime("%d. %B %Y")
    }
    
    return render(request, "meine_app/zeituebersicht.html", context)

# Import - Kristina Baotic 
def import_berichte(request):
    if "username" not in request.session:
        return redirect("login")

    if request.session.get("user_role") not in ["vip", "admin"]:
        return redirect("dashboard")
    
    if request.method != "POST":
        return redirect("vip_datenmanagement")
    
    username = request.session.get("username")

    if 'file' not in request.FILES:
        return redirect("vip_datenmanagement")
    
    hochgeladene_datei = request.FILES['file']
    
    try:
        datei_inhalt = hochgeladene_datei.read().decode('utf-8')
    except:
        return redirect("vip_datenmanagement")
    
    datei_endung = hochgeladene_datei.name.split('.')[-1].lower()

    neue_berichte = []

    if datei_endung == 'json':
        try:
            importierte_daten = json.loads(datei_inhalt)
            if isinstance(importierte_daten, list):
                for bericht in importierte_daten:
                    bericht['benutzer'] = username
                    neue_berichte.append(bericht)
        except:
            return redirect("vip_datenmanagement")

    elif datei_endung == 'csv':
        zeilen = datei_inhalt.split('\n')
        for zeile in zeilen[1:]:
            if zeile.strip():
                teile = zeile.split(';')
                if len(teile) >= 5:
                    neue_berichte.append({
                        'datum': teile[0],
                        'stunden': teile[1],
                        'minuten': teile[2],
                        'modul': teile[3],
                        'beschreibung': teile[4],
                        'benutzer': username
                    })
    else:
        return redirect("vip_datenmanagement")

    if len(neue_berichte) == 0:
        return redirect("vip_datenmanagement")

   
    if os.path.exists(BERICHTE_DATEI):
        with open(BERICHTE_DATEI, "r", encoding='utf-8') as datei:
            try:
                alle_berichte = json.load(datei)
            except:
                alle_berichte = []
    else:
        alle_berichte = []


    bereinigte_berichte = []
    for bericht in alle_berichte:
        if bericht.get("benutzer") != username:
            bereinigte_berichte.append(bericht)

    bereinigte_berichte.extend(neue_berichte)
    
    with open(BERICHTE_DATEI, "w", encoding='utf-8') as datei:
        json.dump(bereinigte_berichte, datei, ensure_ascii=False)
    
    return redirect("dashboard")


def bericht_loeschen(request, index):
    if "username" not in request.session:
        return redirect("/login")
    
    if os.path.exists(BERICHTE_DATEI):
        with open(BERICHTE_DATEI, "r") as datei:
            try:
                berichte = json.load(datei)
            except:
                berichte = []
    else:
        berichte = []

    if 0 <= index < len(berichte):
        berichte.pop(index)
        
        with open(BERICHTE_DATEI, "w") as datei:
            json.dump(berichte, datei, indent=2)
    
    return redirect("dashboard")

def bericht_bearbeiten(request, index):
    if "username" not in request.session:
        return redirect("/login")
    
    if os.path.exists(BERICHTE_DATEI):
        with open(BERICHTE_DATEI, "r") as datei:
            try:
                berichte = json.load(datei)
            except:
                berichte = []
    else:
        berichte = []
    
    if index < 0 or index >= len(berichte):
        return redirect("dashboard")
    
    bericht = berichte[index]
    
    if request.method == "POST":
        berichte[index] = {
            "datum": request.POST.get("datum", ""),
            "stunden": request.POST.get("stunden", ""),
            "minuten": request.POST.get("minuten", ""),
            "modul": request.POST.get("modul", ""),
            "beschreibung": request.POST.get("beschreibung", ""),
            "benutzer": bericht.get("benutzer", "unbekannt")
        }
        
        with open(BERICHTE_DATEI, "w") as datei:
            json.dump(berichte, datei, indent=2)
        
        return redirect("dashboard")
    
    module = load_module() 
    
    context = {
        "user": {
            "role": request.session.get("user_role", "user"),
            "initials": get_initials(
                request.session.get("user_firstname", ""),
                request.session.get("user_lastname", "")
            )
        },
        "bericht": bericht,
        "index": index,
        "module": module 
    }
    
    return render(request, "meine_app/bericht_bearbeiten.html", context)

def load_module():
    if os.path.exists(MODULE_DATEI):
        with open(MODULE_DATEI, "r", encoding="utf-8") as datei:
            try:
                return json.load(datei)
            except:
                return []
    return []

def save_module(module):
    with open(MODULE_DATEI, "w", encoding="utf-8") as datei:
        json.dump(module, datei, indent=2, ensure_ascii=False)

#Modulverwaltung Admin - Kristina Baotic
def admin_modulverwaltung(request):
    if "username" not in request.session:
        return redirect("login")
    
    if request.session.get("user_role") != "admin":
        return redirect("dashboard")
    
    module = load_module()
    
    context = {
        "user": {
            "role": request.session.get("user_role", "user"),
            "initials": get_initials(
                request.session.get("user_firstname", ""),
                request.session.get("user_lastname", "")
            )
        },
        "module": module
    }
    
    return render(request, "meine_app/admin_modulverwaltung.html", context)

def modul_erstellen(request):
    if "username" not in request.session:
        return redirect("login")
    
    if request.session.get("user_role") != "admin":
        return redirect("dashboard")
    
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        beschreibung = request.POST.get("beschreibung", "").strip()
        
        if not name:
            return redirect("admin_modulverwaltung")
        
        module = load_module()
        
        modul_id = name.lower().replace(" ", "_").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
       
        counter = 1
        original_id = modul_id
        while any(m["id"] == modul_id for m in module):
            modul_id = f"{original_id}_{counter}"
            counter += 1
        
        neues_modul = {
            "id": modul_id,
            "name": name,
            "beschreibung": beschreibung,
            "erstellt_am": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "erstellt_von": request.session.get("username")
        }
        
        module.append(neues_modul)
        save_module(module)
        
        return redirect("admin_modulverwaltung")
    
    context = {
        "user": {
            "role": request.session.get("user_role", "user"),
            "initials": get_initials(
                request.session.get("user_firstname", ""),
                request.session.get("user_lastname", "")
            )
        }
    }
    
    return render(request, "meine_app/modul_erstellen.html", context)

def modul_loeschen(request, modul_id):
    if "username" not in request.session:
        return redirect("login")
    
    if request.session.get("user_role") != "admin":
        return redirect("dashboard")
    
    module = load_module()
    
    module = [m for m in module if m["id"] != modul_id]
    save_module(module)
    
    return redirect("admin_modulverwaltung")


#Cookies

def cookie_hinweis_akzeptieren(request):
    response = JsonResponse({"success": True})
    response.set_cookie("cookie_hinweis_gesehen", "true", max_age=365*24*60*60)  # 1 Jahr
    return response
 