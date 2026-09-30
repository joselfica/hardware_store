# 🖥️ Hardware Store — Tienda de Componentes PC

> API REST para e-commerce de componentes informáticos, desarrollada con **Django REST Framework** y **PostgreSQL**. Incluye autenticación JWT con roles, carro de compras persistente, control transaccional de stock, panel de administración completo y frontend HTML/CSS/JS.

[![Django](https://img.shields.io/badge/Django-5.x-092E20?style=flat-square&logo=django)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.15-red?style=flat-square)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-336791?style=flat-square&logo=postgresql)](https://www.postgresql.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)](https://www.python.org/)

---

## 📑 Tabla de Contenidos

- [Descripción](#-descripción)
- [Stack Técnico](#-stack-técnico)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación](#-instalación)
- [Credenciales de Prueba](#-credenciales-de-prueba)
- [Funcionalidades](#-funcionalidades)
- [Documentación API](#-documentación-api)
- [Modelos Principales](#️-modelos-principales)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Seguridad](#-seguridad)
- [Decisiones de Diseño](#-decisiones-de-diseño)
- [Mejoras Futuras](#-mejoras-futuras)
- [Autor](#-autor)

---

## 📖 Descripción

**Hardware Store** es una plataforma de e-commerce especializada en componentes informáticos (procesadores, tarjetas de video, memorias RAM, almacenamiento, etc.). El sistema distingue dos roles claramente diferenciados:

- **Cliente**: explora el catálogo, gestiona su carro de compras persistente, realiza checkout y paga sus órdenes.
- **Administrador de TI**: gestiona el catálogo completo (categorías, marcas, productos), supervisa las órdenes y administra usuarios.

El proyecto implementa reglas de negocio reales como el **descuento de stock solo al confirmar el pago**, **reposición automática al cancelar** y **bloqueo pesimista para evitar sobreventa** en compras concurrentes.

---

## 🚀 Stack Técnico

| Capa | Tecnología |
|------|-----------|
| **Backend** | Django 5.x + Django REST Framework 3.15 |
| **Base de datos** | PostgreSQL 14+ |
| **Autenticación** | JWT (djangorestframework-simplejwt) |
| **Filtros** | django-filter |
| **Documentación** | drf-spectacular (Swagger / OpenAPI 3.0) |
| **Frontend** | HTML5 + Bootstrap 5 + JavaScript vanilla |
| **Configuración** | python-decouple (.env) |
| **Imágenes** | Pillow |
| **CORS** | django-cors-headers |

---

## 📋 Requisitos Previos

Antes de instalar, asegúrate de tener:

- **Python** 3.11 o superior
- **PostgreSQL** 14 o superior en ejecución
- **pip** (gestor de paquetes de Python)
- **git** para clonar el repositorio

---

## ⚙️ Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/joselfica/hardware_store.git
cd hardware_store
