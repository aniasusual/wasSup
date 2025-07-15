import { useAuth } from "../contexts/Auth";
import axios from "axios";

export interface DeploymentInfo {
    id: string;
    name: string;
    display_name: string;
    status: string;
    type: string;
    created_at?: string;
    updated_at?: string;
    region?: string;
    location?: string;
    url?: string;
    service_id?: string;
    node_count?: number;
    version?: string;
    zone?: string;
    machine_type?: string;
    runtime?: string;
    schedule?: string;
}

export interface DeploymentResponse {
    deployments: DeploymentInfo[];
    service_id: string;
    project_id: string;
    count: number;
}

export const useDeploymentService = () => {
    const { token } = useAuth();

    const fetchDeployments = async (
        projectId: string,
        serviceId: string
    ): Promise<any> => {
        if (!token) {
            throw new Error("No authentication token available");
        }

        try {
            const response = await axios.get(
                `/api/v1/logs/deployments/${projectId}/${serviceId}`,
                {
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            return response.data as DeploymentResponse;
        } catch (error: any) {
            if (error.response && error.response.data && error.response.data.detail) {
                throw new Error(error.response.data.detail);
            }
            console.error("Error fetching deployments:", error);
            throw error;
        }
    };

    return {
        fetchDeployments,
    };
}; 