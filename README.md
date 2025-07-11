# AlarmDecoder Custom Integration for Home Assistant

Este es un componente personalizado para integrar AlarmDecoder con Home Assistant, permitiendo manejar múltiples paneles (keypads) según su dirección.

---

## Estado

⚠️ **En desarrollo** – Esta integración aún **no es funcional** y está en proceso de implementación.

---

## Características planificadas

- Soporte para múltiples paneles de alarma (keypads).
- Filtrado de mensajes para cada panel según su dirección.
- Servicios personalizados para comandos de alarma.
- Integración completa con Home Assistant.

---

## Funcionalidades futuras

### Bypass automáticos de zona

Esta integración planea implementar la función de bypass automático de zonas mediante la creación de entidades individuales para cada zona configurable.

- Cada zona susceptible a bypass tendrá su propia entidad en Home Assistant (tipo `switch` o `binary_sensor`).
- Estas entidades permitirán activar o desactivar el bypass manualmente desde la interfaz.
- La integración enviará los comandos correspondientes a la alarma para aplicar o remover el bypass.
- Al armar la alarma, se respetarán las zonas con bypass activado, automatizando la configuración.
- La configuración permitirá seleccionar qué zonas estarán disponibles para bypass.

Esto facilitará el manejo dinámico y personalizado del bypass de zonas, mejorando la experiencia y control del sistema de alarma.

---

## Instalación

Por ahora no hay una versión lista para instalar. Próximamente se publicará un paquete o instrucciones para instalarlo manualmente.

---

## Uso

- Configurar las direcciones de los keypads en el archivo de configuración.
- Añadir la integración en Home
