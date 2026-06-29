from django.db import models
from django.contrib.auth.models import User

class Conversacion(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=200, default='Nueva conversación')
    creada = models.DateTimeField(auto_now_add=True)
    actualizada = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-actualizada']

    def __str__(self):
        return f"{self.usuario.username} - {self.nombre}"

class Mensaje(models.Model):
    conversacion = models.ForeignKey(Conversacion, on_delete=models.CASCADE, related_name='mensajes')
    tipo = models.CharField(max_length=10)  # 'usuario' o 'ia'
    texto = models.TextField()
    peliculas = models.JSONField(default=list)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['creado'] 