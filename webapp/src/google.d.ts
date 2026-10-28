interface Window {
  google?: {
    accounts?: {
      id?: {
        initialize: (...args: any[]) => void;
        prompt: (...args: any[]) => void;
      };
    };
  };
}
