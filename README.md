# 🖥️ Hardware Store — API REST E-commerce (Django + AWS)

> Plataforma backend profesional para una tienda de componentes informáticos. Desarrollada con **Django REST Framework**, desplegada en **AWS EC2** con **HTTPS**, e integrada con la pasarela de pagos real **Transbank Webpay Plus**.

[![Django](https://img.shields.io/badge/Django-5.x-092E20?style=flat-square&logo=django)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.15-red?style=flat-square)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-336791?style=flat-square&logo=postgresql)](https://www.postgresql.org/)
[![AWS](https://img.shields.io/badge/AWS-EC2%20%7C%20RDS-FF9900?style=flat-square&logo=amazon-aws)](https://aws.amazon.com/)
[![Transbank](https://img.shields.io/badge/Transbank-Webpay%20Plus-red?style=flat-square)](https://www.transbankdevelopers.cl/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)](https://www.python.org/)

---

## 📑 Tabla de Contenidos

- [Descripción](#-descripción)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Stack Técnico](#-stack-técnico)
- [Funcionalidades Principales](#-funcionalidades-principales)
- [Seguridad y Roles (RBAC)](#-seguridad-y-roles-rbac)
- [Instalación Local](#-instalación-local)
- [Despliegue en Producción (AWS)](#-despliegue-en-producción-aws)
- [Documentación API](#-documentación-api)
- [Modelos Principales](#️-modelos-principales)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Decisiones de Diseño](#-decisiones-de-diseño)
- [Roadmap / Mejoras Futuras](#-roadmap--mejoras-futuras)
- [Autor](#-autor)

---

## 📖 Descripción

**Hardware Store** es un e-commerce B2C especializado en componentes informáticos. El sistema resuelve problemas reales del negocio retail, como la **persistencia del carro**, la **concurrencia en el control de stock** y la **integración de pagos financieros**.

El sistema distingue dos roles:
- **Cliente**: explora el catálogo, gestiona su carro persistente, realiza checkout, paga con Webpay y gestiona su perfil.
- **Administrador de TI**: gestiona el inventario, el catálogo, las órdenes y los usuarios.

---

## 🏗️ Arquitectura del Sistema

El proyecto está diseñado con una arquitectura desacoplada (Headless API), donde el backend expone servicios REST y el frontend consume los datos mediante JavaScript puro.

**Flujo de Producción Actual:**
```text
[Cliente] 
   │ 
   ▼ (HTTPS)
[DuckDNS (Dominio)] 
   │ 
   ▼
[Nginx (Proxy Inverso)] 
   │ 
   ▼ (Socket Unix)
[Gunicorn (WSGI)] ─── [Django REST Framework]
   │
   ▼
[PostgreSQL (Base de Datos)]
