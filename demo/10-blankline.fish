functions -q __orig_prompt; or functions -c fish_prompt __orig_prompt
function fish_prompt
    printf "\n"
    __orig_prompt
end
