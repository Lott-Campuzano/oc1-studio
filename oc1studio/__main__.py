# punto de entrada de `python -m oc1studio`: solo delega en cli.main()
from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())   # main() devuelve el código de salida (int)
