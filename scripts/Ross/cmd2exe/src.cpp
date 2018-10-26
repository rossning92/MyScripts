#include <iostream>  
#include <Windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <fstream>
#include <string.h>
#include <sstream>
#include <string>
#include <vector>

#define TAG        "EXEC"
#define BUFF_SIZE  256

using namespace std;

bool writeExecutable(const string& srcExe, const string& outExe, int i, int argc, char ** argv)
{
    if (!CopyFile(srcExe.c_str(), outExe.c_str(), FALSE))
    {
        cout << "Cannot copy file." << endl;
        return 1;
    }

    ofstream ofs(outExe, ios::app);
    if (!ofs)
    {
        cout << "Error: cannot open file for writing: " << outExe << endl;
        return false;
    }

    stringstream ss;
    for (int j = i; j < argc; j++)
    {
        if (j > i) ss << " ";

        if (strstr(argv[j], " ") == nullptr)
        {
            ss << argv[j];
        }
        else
        {
            ss << "\"" << argv[j] << "\"";
        }
    }

    auto str = ss.str();
    ofs.write(str.data(), str.size());

    int size = (int)str.size();
    ofs.write((char*)&size, 4);

    ofs.write(TAG, 4);

    cout << "File write successfully: " << outExe << endl;
    return true;
}

int main(int argc, char** argv)
{
    char currentExe[BUFF_SIZE];
    int ret = GetModuleFileNameA(NULL, currentExe, BUFF_SIZE);
    if (ret == 0) {
        cout << "Error: GetModuleFileNameA() failed" << endl;
        return 1;
    }

    char drive[BUFF_SIZE];
    char dir[BUFF_SIZE];
    char fname[BUFF_SIZE];
    char ext[BUFF_SIZE];
    _splitpath_s(currentExe, drive, BUFF_SIZE, dir, BUFF_SIZE, fname, BUFF_SIZE, ext, BUFF_SIZE);

    // Set working directory
    char exeDir[BUFF_SIZE];
    sprintf_s(exeDir, BUFF_SIZE, "%s%s", drive, dir);
    if (!SetCurrentDirectory(exeDir))
    {
        cout << "Error: failed to set current directory to: " << exeDir << endl;
        return 1;
    }

    ifstream ifs(currentExe);
    ifs.seekg(0, ifs.end);
    ifs.seekg(-4, ios::cur);
    char buff[5] = { 0 };
    ifs.read(buff, 4);
    ifs.seekg(-4, ios::cur);

    if (strcmp(buff, TAG) == 0)
    {
        ifs.seekg(-4, ios::cur);
        size_t size;
        ifs.read((char*)&size, 4);
        ifs.seekg(-4, ios::cur);

        ifs.seekg(-(int)size, ios::cur);
        vector<char> command(size + 1, '\0');
        ifs.read(command.data(), size);

        cout << "Run command: " << command.data() << endl;
        return system(command.data());
    }
    else
    {
        string outFile;

        // Parse command line arguments
        for (int i = 1; i < argc; i++)
        {
            if (strcmp(argv[i], "-o") == 0)
            {
                if (i + 1 >= argc)
                {
                    cout << "Error: no argument after -o" << endl;
                    return 1;
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

                if (writeExecutable(currentExe, outFile, i + 1, argc, argv))
                    return 0;
                else
                    return 1;
            }
        }

        cout << "Error: please check parameters" << endl;
        return 1;
    }
}