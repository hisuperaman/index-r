import IndexR from "@/api/IndexR.ts";
import type {ApiToken, McpServer} from "@/models";

export class Integrations extends IndexR {

    public static readonly url = "/api/integrations";

    public static mcpServer(): Promise<McpServer> {
        return this.get(`${Integrations.url}/mcp/`);
    }

    public static listTokens(): Promise<ApiToken[]> {
        return this.get(`${Integrations.url}/tokens/`);
    }

    public static createToken(name: string): Promise<ApiToken> {
        return this.post(`${Integrations.url}/tokens/`, {name});
    }

    public static revokeToken(id: string): Promise<void> {
        return this.delete(`${Integrations.url}/tokens/${id}/`);
    }
}
