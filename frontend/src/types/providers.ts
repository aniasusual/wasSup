export interface CloudProvider {
    id: string;
    name: string;
    icon: string;
    description: string;
    isEnabled: boolean;
    color: string;
}

export const CLOUD_PROVIDERS: CloudProvider[] = [
    {
        id: "gcp",
        name: "Google Cloud Platform",
        icon: "☁️",
        description: "Google Cloud Platform services and resources",
        isEnabled: true,
        color: "from-blue-500 to-green-500"
    },
    {
        id: "aws",
        name: "Amazon Web Services",
        icon: "☁️",
        description: "Amazon Web Services cloud infrastructure",
        isEnabled: false,
        color: "from-orange-500 to-yellow-500"
    },
    {
        id: "azure",
        name: "Microsoft Azure",
        icon: "☁️",
        description: "Microsoft Azure cloud platform",
        isEnabled: false,
        color: "from-blue-600 to-purple-600"
    },
    {
        id: "digitalocean",
        name: "DigitalOcean",
        icon: "☁️",
        description: "DigitalOcean cloud infrastructure",
        isEnabled: false,
        color: "from-blue-400 to-blue-600"
    },
    {
        id: "heroku",
        name: "Heroku",
        icon: "☁️",
        description: "Heroku cloud application platform",
        isEnabled: false,
        color: "from-purple-500 to-pink-500"
    }
]; 