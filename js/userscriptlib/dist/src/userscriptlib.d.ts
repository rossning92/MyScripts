export declare function addButton(name: string, onclick: () => void, hotkey?: string): void;
export declare function addText(text: string, { color }?: {
    color?: string;
}): void;
export declare function findElementByXPath(exp: string): Node;
export declare function findElementByText(text: string): Node;
export declare function waitForSelector(selector: string): Promise<unknown>;
export declare function waitForText(text: string): Promise<unknown>;
export declare function waitForXPath(xpath: string): Promise<unknown>;
declare global {
    interface Navigator {
        msSaveOrOpenBlob: any;
    }
}
export declare function saveAsFile(data: string, filename: string, type?: string): void;
export declare function download(url: string, filename?: string): void;
export declare function openInNewWindow(url: string): void;
