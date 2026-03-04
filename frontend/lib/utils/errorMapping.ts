export const errorMessages: Record<string, string> = {
  REGISTRATION_FAILED: "Не удалось завершить регистрацию. Попробуйте другие данные.",
  
  INVALID_CODE: "Неверный код подтверждения. Попробуйте еще раз.",
  VERIFICATION_CODE_EXPIRED: "Превышено количество попыток. Запросите новый код.",
  
  INVALID_CREDENTIALS: "Неверный email или пароль.",
  EMAIL_NOT_VERIFIED: "Email не подтвержден. Проверьте почту.",
  
  INTERNAL_ERROR: "Произошла ошибка. Попробуйте позже.",
  SERVICE_UNAVAILABLE: "Сервис временно недоступен. Попробуйте позже.",
  UNAUTHORIZED: "Требуется авторизация.",
  TOKEN_REVOKED: "Токен недействителен. Войдите заново.",
  REFRESH_TOKEN_EXPIRED: "Сессия истекла. Войдите заново.",
  RATE_LIMIT_EXCEEDED: "Слишком много запросов. Подождите немного.",
};

export function mapErrorToMessage(errorCode: string): string {
  return errorMessages[errorCode] || errorMessages.INTERNAL_ERROR;
}
