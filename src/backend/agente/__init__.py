"""Agente conversacional de AURA (LangChain + Ollama).

Este paquete no importa `app/` ni `aura/`: habla con la agenda a través del puerto
`agente.puerto.PuertoAgenda`, que implementa la plataforma. Importar `agente` no carga
LangChain; los módulos que lo necesitan lo hacen al importarse.
"""
