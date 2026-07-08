export class ApiError extends Error {
  readonly status: number;
  readonly userMessage: string;

  constructor(status: number, userMessage: string, debugDetail?: string) {
    super(debugDetail ?? userMessage);
    this.name = "ApiError";
    this.status = status;
    this.userMessage = userMessage;
  }
}

const STATUS_MESSAGES: Record<number, string> = {
  400: "요청 형식이 올바르지 않습니다. 설정을 확인한 뒤 다시 시도해 주세요.",
  404: "스크리너 API를 찾을 수 없습니다. 배포 설정(BACKEND_URL)을 확인해 주세요.",
  422: "요청 조건이 맞지 않습니다. 시장·유니버스 설정을 바꾼 뒤 다시 시도해 주세요.",
  429: "요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.",
  500: "서버에서 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
  502: "백엔드 서버에 연결하지 못했습니다. Render 서비스가 켜져 있는지 확인해 주세요.",
  503: "서버가 일시적으로 사용 불가합니다. cold start 중일 수 있으니 1~2분 후 다시 시도해 주세요.",
  504: "응답 시간이 초과되었습니다. 유니버스 종목 수를 줄이거나 잠시 후 다시 시도해 주세요.",
};

export function userMessageForStatus(status: number): string {
  return (
    STATUS_MESSAGES[status] ??
    "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."
  );
}

export function getUserErrorMessage(
  error: unknown,
  fallback = "스크리닝 데이터를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요."
): string {
  if (error instanceof ApiError) {
    return error.userMessage;
  }
  if (error instanceof TypeError) {
    return "네트워크 연결에 실패했습니다. 인터넷 연결을 확인한 뒤 다시 시도해 주세요.";
  }
  if (error instanceof Error) {
    if (/failed to fetch|network|abort/i.test(error.message)) {
      return "서버에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.";
    }
  }
  return fallback;
}
