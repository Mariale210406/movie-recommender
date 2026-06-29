from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json, sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.chatbot import responder
from .models import Conversacion, Mensaje

def generar_nombre(mensaje):
    mensaje = mensaje.lower()
    if 'como' in mensaje or 'similar' in mensaje:
        return f"Similares a {mensaje.split()[-1].capitalize()}"
    elif 'director' in mensaje or 'hizo' in mensaje:
        return f"Director: {mensaje.split()[-1].capitalize()}"
    elif 'disney' in mensaje:
        return "Películas de Disney"
    elif 'familia' in mensaje or 'niños' in mensaje:
        return "Para ver en familia"
    elif 'terror' in mensaje or 'miedo' in mensaje:
        return "Películas de terror"
    elif 'comedia' in mensaje or 'reir' in mensaje or 'reír' in mensaje:
        return "Películas para reír"
    elif 'sorprende' in mensaje or 'recomienda' in mensaje:
        return "Recomendación sorpresa"
    elif 'español' in mensaje:
        return "Películas en español"
    elif 'familia' in mensaje:
        return "Para ver en familia"
    else:
        palabras = mensaje.strip().split()
        nombre = ' '.join(palabras[:4]).capitalize()
        return nombre if nombre else "Nueva conversación"

@login_required
def inicio(request):
    conversaciones = Conversacion.objects.filter(usuario=request.user)
    return render(request, 'recommender/chat.html', {
        'conversaciones': conversaciones,
        'conversacion_activa': None,
        'mensajes': []
    })

@login_required
def ver_conversacion(request, conv_id):
    conversacion = get_object_or_404(Conversacion, id=conv_id, usuario=request.user)
    conversaciones = Conversacion.objects.filter(usuario=request.user)
    mensajes = conversacion.mensajes.all()
    return render(request, 'recommender/chat.html', {
        'conversaciones': conversaciones,
        'conversacion_activa': conversacion,
        'mensajes': mensajes
    })

@login_required
def chat_responder(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mensaje = data.get('mensaje', '')
            conv_id = data.get('conv_id', None)

            # Obtener o crear conversación
            if conv_id:
                conversacion = get_object_or_404(Conversacion, id=conv_id, usuario=request.user)
            else:
                nombre = generar_nombre(mensaje)
                conversacion = Conversacion.objects.create(
                    usuario=request.user,
                    nombre=nombre
                )

            # Guardar mensaje del usuario
            Mensaje.objects.create(
                conversacion=conversacion,
                tipo='usuario',
                texto=mensaje,
                peliculas=[]
            )

            # Obtener respuesta de la IA
            resultado = responder(mensaje)
            if isinstance(resultado, str):
                resultado = {'texto': resultado, 'peliculas': []}

            # Guardar respuesta de la IA
            Mensaje.objects.create(
                conversacion=conversacion,
                tipo='ia',
                texto=resultado.get('texto', ''),
                peliculas=resultado.get('peliculas', [])
            )

            resultado['conv_id'] = conversacion.id
            resultado['conv_nombre'] = conversacion.nombre
            return JsonResponse(resultado)

        except Exception as e:
            return JsonResponse({'texto': f'Error: {str(e)}', 'peliculas': []})

    return JsonResponse({'error': 'Método no permitido'})

def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')
    else:
        form = UserCreationForm()
    return render(request, 'recommender/registro.html', {'form': form})
