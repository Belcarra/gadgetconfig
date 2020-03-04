

all:
	@echo "make sdist | install | bdist | twine"


clean:
	rm -f */*pyc
	rm -rf build dist qlmux.egg-info

.PHONY: sdist install bdist


bdist:
	python3 setup.py $@
sdist:
	python3 setup.py $@
#install:
#	python3 setup.py $@
install:
	pip3 install --upgrade .
uninstall:
	pip3 uninstall gadgetconfig

twine:
	twine upload dist/*

twine-test:
	twine check dist/*


flake8a:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

flake8b:
	flake8 . --ignore=C901,E701,E117,W191,E128 --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

doctest:
	python3 -m doctest src/sysfstree/__init__.py -v


gadget_modules.tgz:
	cd /; tar cvfz /tmp/$@ \
		lib/modules/4.19.97-v7l+/kernel/drivers/usb/gadget/function/u_serial.ko \
		lib/modules/4.19.97-v7l+/kernel/drivers/usb/gadget/function/u_ether.ko \
		lib/modules/4.19.97-v7l+/kernel/drivers/usb/gadget/function/usb_f_acm.ko \
		lib/modules/4.19.97-v7l+/kernel/drivers/usb/gadget/function/usb_f_ecm.ko \
		lib/modules/4.19.97-v7l+/kernel/drivers/usb/dwc2 \
		lib/modules/4.19.97-v7l+/kernel/drivers/usb/mon 
		mv /tmp/$@ .

sysfs.tgz:
	cd /; tar cvfz /tmp/$@ \
		mv /tmp/$@ .


