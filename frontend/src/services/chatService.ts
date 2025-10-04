import axios from "axios";
import toast from "react-hot-toast";


export interface ChatTurnRequestPayload {
  message: string;
  sessionId?: string;
  projectId?: string;
  context?: Record<string, unknown>;
}

export const sendChatTurn = async (
  payload: ChatTurnRequestPayload,
  token: string
) => {
  try {
    const response = await axios.post(
      "/api/v1/conversations/respond",
      {
        message: payload.message,
        session_id: payload.sessionId,
        project_id: payload.projectId,
        context: payload.context ?? {},
      },
      {
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      }
    );

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status;
      if (status === 401 || status === 403) {
        toast.error("Session expired. Please log in again.");
        window.setTimeout(() => {
          window.location.replace("/login");
        }, 200);
      }
    }

    throw error;
  }
};
