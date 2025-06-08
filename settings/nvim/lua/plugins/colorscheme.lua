return {
    {
        'Mofiqul/dracula.nvim',
        priority = 1000, -- Make sure to load this before all the other start plugins.
        config = function()
            require("dracula").setup({
                transparent_bg = true,
            })

            vim.cmd.colorscheme 'dracula'
        end,
    },
}
