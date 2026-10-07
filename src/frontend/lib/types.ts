// Tipos del dominio AURA. Ajusta estos campos cuando Camilo y Leo
// confirmen el contrato real del backend (ver README, sección "Endpoints").
// Los tipos de la vista de Coordinación están en ./types-coordinacion.ts.

export type Role = "user" | "agent";

export interface ChatMessage {
  id: string;
  role: Role;
  text: string;
}

export interface ServiceOption {
  id: string;
  nombre: string;
  modalidad: "presencial" | "online" | "telefónico";
  esperaEstimadaDias: number;
  descripcion: string;
}

export interface TimeSlot {
  id: string;
  serviceId: string;
  fechaISO: string;
  disponible: boolean;
}

export interface Appointment {
  id: string;
  serviceId: string;
  serviceName: string;
  slot: TimeSlot;
  estado: "confirmada" | "lista_de_espera";
}

export interface ChatResponse {
  reply: string;
  services?: ServiceOption[];
}
