"use client";

import { useEffect } from "react";
import Swal, { SweetAlertIcon } from "sweetalert2";

type NotificationType = Extract<SweetAlertIcon, "success" | "warning" | "error">;

type NotificationAlertProps = {
  message: string | null;
  type?: NotificationType;
};

function inferType(message: string): NotificationType {
  return /não |falha|erro|indisponível|inválid/i.test(message) ? "error" : "success";
}

export function NotificationAlert({ message, type }: NotificationAlertProps) {
  useEffect(() => {
    if (!message) return;
    void Swal.fire({
      toast: true,
      position: "top",
      icon: type ?? inferType(message),
      title: message,
      showConfirmButton: false,
      timer: 5000,
      timerProgressBar: true,
      showCloseButton: true,
    });
  }, [message, type]);

  return null;
}
