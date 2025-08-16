// Helper function to parse GCP API error messages and make them user-friendly
export const parseGCPErrorMessage = (errorMessage: string): string => {
    // Check for common GCP API errors and provide user-friendly messages
    if (errorMessage.includes("SERVICE_DISABLED")) {
        if (errorMessage.includes("cloudresourcemanager.googleapis.com")) {
            return "Cloud Resource Manager API is disabled. Please enable it in your GCP project.";
        }
        if (errorMessage.includes("logging.googleapis.com")) {
            return "Cloud Logging API is disabled. Please enable it in your GCP project.";
        }
        return "Required GCP API is disabled. Please enable it in your GCP project.";
    }

    if (errorMessage.includes("PERMISSION_DENIED")) {
        return "Permission denied. Please check your GCP project permissions.";
    }

    if (errorMessage.includes("NOT_FOUND")) {
        return "Project not found. Please check your GCP project ID.";
    }

    if (errorMessage.includes("INVALID_ARGUMENT")) {
        return "Invalid request. Please check your parameters.";
    }

    // For other errors, try to extract the main message
    const lines = errorMessage.split('\n');
    for (const line of lines) {
        if (line.includes('message') && line.includes('"')) {
            const match = line.match(/"([^"]+)"/);
            if (match) {
                return match[1];
            }
        }
    }

    // Fallback: return first 100 characters of the error
    return errorMessage.length > 100 ? errorMessage.substring(0, 100) + "..." : errorMessage;
};
