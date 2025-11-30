export {};
declare global {
    interface Navigator {
        msSaveOrOpenBlob: any;
    }
    var GM_xmlhttpRequest: any;
    function addButton(name: string, onclick: () => void, hotkey?: string): void;
    function highlight(el: HTMLElement, text?: string): void;
    function addText(text: string, { color }: {
        color?: string;
    }): void;
    function click(el: HTMLElement): void;
    function debug(): void;
    function download(url: string, filename?: string): void;
    function findElementByPartialText(text: string): Node | null;
    function findElementBySelector(selector: string): Node | null;
    function findElementByText(text: string): Node | null;
    function findElementsByText(text: string): Node[];
    function findElementByXPath(exp: string): Node | null;
    function findElementsByXPath(exp: string): Node[];
    function getSelectedText(): string;
    function loadData(name: string): Promise<object>;
    function loadFile(file: string): Promise<string>;
    function logd(message: string): void;
    function openInNewWindow(url: string): void;
    function saveData(name: string, data: object): Promise<void>;
    function saveFile(file: string, content: string): Promise<void>;
    function saveTextAsFile(data: string, filename: string, type?: string): void;
    function sendKey(keyCode: number, type?: "up" | "press"): void;
    function sendText(text: string): void;
    function sleep(callback: () => void, ms: number): void;
    function system(args: string | string[]): Promise<string>;
    function waitForPartialText(text: string): Promise<Node>;
    function waitForSelector(selector: string): Promise<Node>;
    function waitForSelectorAll(selector: string): Promise<NodeList>;
    function waitForText(text: string): Promise<Node>;
    function waitForXPath(xpath: string): Promise<Node>;
}
