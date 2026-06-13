
class AuthService {
    public login(username: string, password: string): void {
    }
    
    async register(email: string, password: string): Promise<void> {
    }
    
    private verify_token(token: string): boolean {
        return true;
    }
}
