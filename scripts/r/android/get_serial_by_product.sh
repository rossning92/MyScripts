product_name="$1"

if [ -z "$product_name" ]; then
    exit 1
fi

adb devices -l | while read -r serial state rest; do
    case "$serial" in
    List | "")
        continue
        ;;
    esac

    if [ "$state" != "device" ]; then
        continue
    fi

    case " $rest " in
    *" product:$product_name "*)
        printf "%s" "$serial"
        exit 0
        ;;
    esac
done

exit 1
