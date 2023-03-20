export const entry: string;
export namespace resolve {
    const extensions: string[];
}
export namespace output {
    const path: string;
    const filename: string;
    const libraryTarget: string;
}
export namespace module {
    const rules: {
        test: RegExp;
        use: string;
        exclude: RegExp;
    }[];
}
