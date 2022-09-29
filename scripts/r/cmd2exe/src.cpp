#include <iostream>  
#include <Windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <fstream>
#include <string.h>
#include <sstream>
#include <string>
#include <vector>
#include <assert.h>

const char* TAG = "EXEC";
const int BUFF_SIZE = 1024;

using namespace std;

bool writeExecutable(const string& srcExe, const string& outExe, int i, int argc, char ** argv)
{
    if (!CopyFile(srcExe.c_str(), outExe.c_str(), FALSE))
    {
        cout << "Cannot copy file." << endl;
        return false;
    }

    ofstream ofs(outExe, ios::app);
    if (!ofs)
    {
        cout << "Error: cannot open file for writing: " << outExe << endl;
        return false;
    }

    stringstream args_ss;
    for (int j = i; j < argc; j++)
    {
        if (j > i) args_ss << " ";

        if (strstr(argv[j], " ") == nullptr)
        {
            args_ss << argv[j];
        }
        else
        {
            args_ss << "\"" << argv[j] << "\"";
        }
    }

    auto args = args_ss.str();
    ofs.write(args.data(), args.size());

    int size = (int)args.size();
    ofs.write((char*)&size, 4);

    ofs.write(TAG, 4);

    cout << "File write successfully: " << outExe << endl;
    return true;
}

int main(int argc, char** argv)
{
    char exeFileName[BUFF_SIZE];
    int ret = GetModuleFileNameA(NULL, exeFileName, BUFF_SIZE);
    if (ret == 0) {
        cout << "Error: GetModuleFileNameA() failed" << endl;
        return -1;
    }

    HANDLE hFile = CreateFileA(exeFileName,
        GENERIC_READ,
        0,
        NULL,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        NULL);
    assert(hFile != INVALID_HANDLE_VALUE);

    DWORD dwFileSize = GetFileSize(hFile, NULL);

    HANDLE hMapFile = CreateFileMapping(hFile,
        NULL,           // default security
        PAGE_READONLY,  // read/write permission
        0,              // size of mapping object, high
        dwFileSize,     // size of mapping object, low
        NULL);          // name of mapping object
    assert(hMapFile);

    LPVOID lpMapAddress = MapViewOfFile(hMapFile,
        FILE_MAP_READ,
        0,           // high-order 32 bits of file offset
        0,           // low-order 32 bits of file offset
        dwFileSize); // number of bytes to map
    assert(lpMapAddress);

    char* pCur = (char*)lpMapAddress + dwFileSize - 4;

    // This exe is a proxy exe
    if (strncmp(pCur, TAG, 4) == 0)
    {
        pCur -= 4;
        int size = *((int*)pCur);

        pCur -= size;
        vector<char> command(size + 1, '\0');
        memcpy(command.data(), pCur, size);

        stringstream args_ss;
        args_ss << command.data();
        for (int i = 1; i < argc; i++) // Do not pass first parameter
        {
            args_ss << " ";
            if (strstr(argv[i], " ") == nullptr)
            {
                args_ss << argv[i];
            }
            else
            {
                args_ss << "\"" << argv[i] << "\"";
            }
        }

        cout << "Run command: " << args_ss.str() << endl;
        return system(args_ss.str().c_str());
    }

    // Close memory map of file
    BOOL bFlag = UnmapViewOfFile(lpMapAddress);
    assert(bFlag);

    bFlag = CloseHandle(hMapFile);
    assert(bFlag);

    bFlag = CloseHandle(hFile);
    assert(bFlag);

    string outFile;

    // Parse command line arguments
    for (int i = 1; i < argc; i++)
    {
        if (strcmp(argv[i], "-o") == 0)
        {
            if (i + 1 >= argc)
            {
                cout << "Error: no argument after -o" << endl;
                return -1;
            }
            outFile = argv[i + 1];
            i++;
            continue;
        }
        else if (strcmp(argv[i], "-c") == 0)
        {
            if (outFile.empty())
            {
                cout << "Error: please specify output file by using -o" << endl;
                return -1;
            }

            if (writeExecutable(exeFileName, outFile, i + 1, argc, argv))
                return 0;
            else
                return -1;
        }
    }

    cout << "Error: please check parameters" << endl;
    return -1;
}